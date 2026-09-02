"""文档索引/删除异步 Worker。

独立进程运行（与后端分离），消费 document_task 表中的 index/delete 任务。
启动方式：uv run python -m ai.indexing_worker
"""
import asyncio
import json
import os
import sys
import time
from pathlib import Path
from typing import Optional

# 独立进程运行时加载项目根目录 .env
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(PROJECT_ROOT / ".env")

from ai.ingestion_service import IngestionService  # noqa: E402
from crud.document_crud import DocumentCRUD  # noqa: E402
from crud.document_task_crud import DocumentTaskCRUD  # noqa: E402
from model.document_model import Document  # noqa: E402
from util.db_util import get_connection  # noqa: E402
from util.oss_util import OSSUtil  # noqa: E402
from util.file_util import chunk_text_by_sentence, read_file_content  # noqa: E402

WORKER_ID = f"worker-{os.getpid()}"
POLL_INTERVAL = float(os.getenv("INDEX_WORKER_POLL_INTERVAL", "2"))
IDLE_SLEEP = float(os.getenv("INDEX_WORKER_IDLE_SLEEP", "3"))
MAX_EMPTY_LOOPS = 30  # 连续空转 N 次后短暂休眠，降低对 DB 的轮询压力


def _extract_text_from_oss(object_key: str, filename: str) -> Optional[str]:
    """
    从 OSS 拉取文件内容并解析为纯文本
    :param object_key: OSS 对象 key
    :param filename: 原始文件名（用于判断文件类型）
    :return: 纯文本内容，解析失败返回 None
    """
    import asyncio as _asyncio

    async def _inner():
        async with OSSUtil() as oss_client:
            result = await oss_client.get_file(object_key)
            if not result.get("exists"):
                return None
            content = result["content"]
        # 复用 file_util 的解析逻辑（通过 UploadFile 兼容对象适配）
        from fastapi import UploadFile

        class _BytesFile:
            """极简 UploadFile 兼容对象，仅提供 read/seek/filename"""
            def __init__(self, data: bytes, name: str):
                self._data = data
                self._pos = 0
                self.filename = name

            async def read(self, size: int = -1) -> bytes:
                if size < 0:
                    data = self._data[self._pos:]
                    self._pos = len(self._data)
                    return data
                data = self._data[self._pos:self._pos + size]
                self._pos += len(data)
                return data

            async def seek(self, offset: int) -> None:
                self._pos = offset

        fake = _BytesFile(content, filename)
        return await read_file_content(fake)

    return _asyncio.run(_inner())


def _parse_filename_ext(filename: str) -> str:
    return filename.split(".")[-1].lower() if "." in filename else ""


def _handle_index_task(task_id: int, document_id: int, kb_id: int, payload: dict) -> None:
    """
    处理单个索引任务。
    分块在 Worker 内从 OSS 拉取原始内容后解析（不依赖上传请求上下文）。
    """
    object_key = payload.get("object_key", "")
    filename = payload.get("filename", "")

    # 1. 标记文档为索引中（幂等）
    DocumentCRUD.update_status(document_id, "indexing")

    # 2. 从 OSS 拉取内容并解析
    text = _extract_text_from_oss(object_key, filename)
    if text is None:
        # 解析失败（可能是 OSS 404 或文件无法解析），按失败处理
        raise RuntimeError(f"从 OSS 读取或解析文档失败：object_key={object_key}")

    chunks = chunk_text_by_sentence(text)
    if not chunks:
        # 空文档：无内容可索引，视为成功（避免留下 pending 状态）
        DocumentCRUD.update_status(document_id, "ready", chunk_count=0)
        DocumentTaskCRUD.mark_done(
            task_id,
            {"chroma": True, "es": True, "chunk_count": 0, "note": "empty_content"}
        )
        return

    # 3. 向量化 + 双写（幂等）
    ingestion = IngestionService()
    ingest_result = ingestion.ingest_document(knowledge_base_id=kb_id, document_id=document_id, chunks=chunks)

    # 4. 依据结果更新状态
    if ingest_result["status"] == "success":
        DocumentCRUD.update_status(
            document_id, "ready",
            chunk_count=ingest_result["chunk_count"],
            error_message=None,
            retry_count=0
        )
        DocumentTaskCRUD.mark_done(
            task_id,
            {
                "chroma": ingest_result["chroma_ok"],
                "es": ingest_result["es_ok"],
                "chunk_count": ingest_result["chunk_count"],
            }
        )
    elif ingest_result["status"] == "partial":
        # 部分成功：本次先按失败重试（幂等补写另一侧），记录中间结果
        raise RuntimeError(
            "索引部分成功（Chroma/ES 一侧失败），等待重试补齐："
            f"chroma={ingest_result['chroma_ok']}, es={ingest_result['es_ok']}"
        )
    else:
        raise RuntimeError("索引全部失败（Chroma 与 ES 均写入失败）")


def _handle_delete_task(task_id: int, document_id: int, kb_id: int, payload: dict) -> None:
    """
    处理单个删除任务：OSS -> Chroma -> ES -> MySQL 记录，逐端幂等删除。
    任一步失败则抛异常由外层安排重试（已成功的步骤幂等，重试无副作用）。
    """
    object_key = payload.get("object_key", "")

    # 1. 删除 OSS 对象（幂等，404 视为已删除）
    if object_key:
        async def _del_oss():
            async with OSSUtil() as oss_client:
                await oss_client.delete_file(object_key)
        asyncio.run(_del_oss())

    # 2. 删除 Chroma + ES 索引（幂等）
    ingestion = IngestionService()
    delete_result = ingestion.delete_document(kb_id, document_id)

    # 3. 删除 MySQL 记录（与任务完成状态一起提交）
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM document WHERE id = %s", (document_id,))
            cursor.execute(
                "UPDATE document_task SET status = 'done', result_json = %s, "
                "error_message = NULL, update_time = NOW() WHERE id = %s",
                (
                    json.dumps(
                        {"oss": True, "chroma": delete_result["chroma"], "es": delete_result["es"]},
                        ensure_ascii=False
                    ),
                    task_id,
                )
            )
        finally:
            cursor.close()


def _handle_delete_kb_task(task_id: int, kb_id: int, payload: dict) -> None:
    """
    处理单个删除知识库任务：Chroma -> ES -> MySQL（文档记录与知识库记录、任务状态一起提交）。
    """
    # 1. 删除 Chroma + ES 索引（幂等）
    ingestion = IngestionService()
    delete_result = ingestion.delete_knowledge_base(kb_id)

    # 2. 删除该知识库下的所有文档记录、知识库记录，并标记任务完成（单事务）
    with get_connection() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM document WHERE knowledge_base_id = %s", (kb_id,))
            cursor.execute("DELETE FROM knowledge_base WHERE id = %s", (kb_id,))
            cursor.execute(
                "UPDATE document_task SET status = 'done', result_json = %s, "
                "error_message = NULL, update_time = NOW() WHERE id = %s",
                (
                    json.dumps(
                        {"chroma": delete_result["chroma"], "es": delete_result["es"], "kb_id": kb_id},
                        ensure_ascii=False
                    ),
                    task_id,
                )
            )
        finally:
            cursor.close()


def process_task(task) -> None:
    """
    处理单个任务，异常时抛出由外层决定重试策略。
    """
    payload = {}
    if task.payload:
        try:
            payload = json.loads(task.payload)
        except json.JSONDecodeError:
            payload = {}

    task_type = task.task_type
    document_id = task.document_id
    kb_id = task.knowledge_base_id

    if task_type == "index":
        _handle_index_task(task.id, document_id, kb_id, payload)
    elif task_type == "delete":
        _handle_delete_task(task.id, document_id, kb_id, payload)
    elif task_type == "delete_kb":
        _handle_delete_kb_task(task.id, kb_id, payload)
    else:
        raise RuntimeError(f"未知任务类型：{task_type}")


def run_once() -> int:
    """
    执行一轮：领取任务并处理。
    :return: 本次处理的任务数量
    """
    claimed = DocumentTaskCRUD.claim_next(task_type="index", worker_id=WORKER_ID, limit=1)
    claimed += DocumentTaskCRUD.claim_next(task_type="delete", worker_id=WORKER_ID, limit=1)
    claimed += DocumentTaskCRUD.claim_next(task_type="delete_kb", worker_id=WORKER_ID, limit=1)

    for task in claimed:
        task_type = task.task_type
        try:
            process_task(task)
            print(f"[Worker] {task_type} task #{task.id} (doc={task.document_id}) done")
        except Exception as e:
            print(f"[Worker] {task_type} task #{task.id} (doc={task.document_id}) failed: {e}")
            final = DocumentTaskCRUD.mark_retry(
                task.id,
                str(e),
                retry_count=task.retry_count + 1,
                max_retries=task.max_retries,
            )
            if task_type == "index":
                if final:
                    DocumentCRUD.update_status(task.document_id, "failed", error_message=str(e)[:2000])
                else:
                    # 仍在重试中，标记为 indexing（等待下次领取）
                    DocumentCRUD.update_status(task.document_id, "indexing", error_message=str(e)[:2000])
            elif task_type in ("delete", "delete_kb"):
                # 删除失败：文档保持 deleting，等待重试；超限记录失败
                if task.document_id and task.document_id > 0:
                    DocumentCRUD.update_status(task.document_id, "deleting", error_message=str(e)[:2000])
        finally:
            # 无论成功与否，短暂等待避免 CPU 空转
            time.sleep(POLL_INTERVAL)

    return len(claimed)


def main_loop() -> None:
    """Worker 主循环"""
    print(f"[Worker] {WORKER_ID} 启动，开始轮询 document_task ...")
    empty_loops = 0
    while True:
        try:
            processed = run_once()
            if processed == 0:
                empty_loops += 1
                if empty_loops >= MAX_EMPTY_LOOPS:
                    time.sleep(IDLE_SLEEP)
                    empty_loops = 0
            else:
                empty_loops = 0
        except KeyboardInterrupt:
            print("[Worker] 收到中断，退出")
            break
        except Exception as e:
            print(f"[Worker] 主循环异常：{e}，5 秒后继续")
            time.sleep(5)


if __name__ == "__main__":
    main_loop()
