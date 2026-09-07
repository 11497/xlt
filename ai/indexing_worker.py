"""文档索引/删除异步 Worker。

独立进程运行（与后端分离），消费 document_task 表中的 index/delete 任务。
启动方式：uv run python -m ai.indexing_worker
"""
import asyncio
import json
import pymysql
import os
import sys
import time
from pathlib import Path
from typing import Optional

# 独立进程运行时确保能导入项目根目录下的 config 包，并触发统一加载 .env。
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config  # noqa: E402

from ai.ingestion_service import IngestionService  # noqa: E402
from crud.document_crud import DocumentCRUD  # noqa: E402
from crud.document_task_crud import DocumentTaskCRUD  # noqa: E402
from model.document_model import Document  # noqa: E402
from util.db_util import get_connection  # noqa: E402
from config.worker_config import WORKER_POLL_INTERVAL, WORKER_IDLE_SLEEP  # noqa: E402
from util.oss_util import OSSUtil  # noqa: E402
from util.file_util import chunk_text_by_sentence, read_file_content  # noqa: E402

WORKER_ID = f"worker-{os.getpid()}"
POLL_INTERVAL = WORKER_POLL_INTERVAL
IDLE_SLEEP = WORKER_IDLE_SLEEP
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


def _mark_index_task_skipped(cursor, task_id: int, reason: str) -> bool:
    cursor.execute(
        "UPDATE document_task SET status = 'done', result_json = %s, "
        "error_message = NULL, claimed_by = NULL, claimed_at = NULL, update_time = NOW() "
        "WHERE id = %s AND status = 'processing' AND claimed_by = %s",
        (json.dumps({"skipped": reason}, ensure_ascii=False), task_id, WORKER_ID),
    )
    return cursor.rowcount == 1


def _validate_index_task(task_id: int, document_id: int, kb_id: int) -> bool:
    """处理索引任务前校验文档和知识库仍可索引，并取消过期索引任务。"""
    with get_connection() as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            cursor.execute(
                "SELECT id FROM knowledge_base WHERE id = %s AND is_deleted = 0 FOR UPDATE",
                (kb_id,)
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    "UPDATE document_task SET status = 'done', result_json = %s, "
                    "error_message = NULL, claimed_by = NULL, claimed_at = NULL, update_time = NOW() "
                    "WHERE id = %s AND status = 'processing' AND claimed_by = %s",
                    (json.dumps({"skipped": "knowledge_base_deleted"}, ensure_ascii=False), task_id, WORKER_ID)
                )
                return False
            cursor.execute(
                "SELECT id, status FROM document WHERE id = %s AND knowledge_base_id = %s "
                "AND is_deleted = 0 FOR UPDATE",
                (document_id, kb_id)
            )
            row = cursor.fetchone()
            if row is None:
                cursor.execute(
                    "UPDATE document_task SET status = 'done', result_json = %s, "
                    "error_message = NULL, claimed_by = NULL, claimed_at = NULL, update_time = NOW() "
                    "WHERE id = %s AND status = 'processing' AND claimed_by = %s",
                    (json.dumps({"skipped": "document_deleted"}, ensure_ascii=False), task_id, WORKER_ID)
                )
                return False
            if row["status"] == "deleting":
                _mark_index_task_skipped(cursor, task_id, "document_deleting")
                return False
            cursor.execute(
                "SELECT id FROM document_task WHERE id = %s AND status = 'processing' "
                "AND claimed_by = %s FOR UPDATE",
                (task_id, WORKER_ID),
            )
            if cursor.fetchone() is None:
                return False
            cursor.execute(
                "UPDATE document SET status = 'indexing', error_message = NULL, update_time = NOW() "
                "WHERE id = %s AND knowledge_base_id = %s AND is_deleted = 0 "
                "AND status NOT IN ('deleting', 'deleted')",
                (document_id, kb_id),
            )
            return cursor.rowcount == 1
        finally:
            cursor.close()


def _finish_index_task(
        task_id: int,
        document_id: int,
        kb_id: int,
        result_json: dict,
        chunk_count: int,
) -> bool:
    """在同一事务内完成文档状态和任务状态，避免删除看到半完成索引。"""
    with get_connection() as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            cursor.execute("SELECT id FROM knowledge_base WHERE id = %s FOR UPDATE", (kb_id,))
            if cursor.fetchone() is None:
                return False
            cursor.execute(
                "SELECT id FROM document WHERE id = %s AND knowledge_base_id = %s "
                "AND is_deleted = 0 AND status = 'indexing' FOR UPDATE",
                (document_id, kb_id),
            )
            if cursor.fetchone() is None:
                return False
            cursor.execute(
                "SELECT id FROM document_task WHERE id = %s AND status = 'processing' "
                "AND claimed_by = %s FOR UPDATE",
                (task_id, WORKER_ID),
            )
            if cursor.fetchone() is None:
                return False
            cursor.execute(
                "UPDATE document SET status = 'ready', error_message = NULL, retry_count = 0, "
                "chunk_count = %s, update_time = NOW() WHERE id = %s AND is_deleted = 0 "
                "AND status = 'indexing'",
                (chunk_count, document_id),
            )
            cursor.execute(
                "UPDATE document_task SET status = 'done', result_json = %s, error_message = NULL, "
                "claimed_by = NULL, claimed_at = NULL, update_time = NOW() "
                "WHERE id = %s AND status = 'processing' AND claimed_by = %s",
                (json.dumps(result_json, ensure_ascii=False), task_id, WORKER_ID),
            )
            if cursor.rowcount != 1:
                raise RuntimeError("索引任务所有权已失效")
            return True
        finally:
            cursor.close()


def _handle_index_task(task_id: int, document_id: int, kb_id: int, payload: dict) -> None:
    """
    处理单个索引任务。
    分块在 Worker 内从 OSS 拉取原始内容后解析（不依赖上传请求上下文）。
    """
    object_key = payload.get("object_key", "")
    filename = payload.get("filename", "")

    # 1. 校验知识库和文档未被删除；过期索引任务标记为 done/skipped。
    if not _validate_index_task(task_id, document_id, kb_id):
        return

    # 3. 从 OSS 拉取内容并解析
    text = _extract_text_from_oss(object_key, filename)
    if text is None:
        # 解析失败（可能是 OSS 404 或文件无法解析），按失败处理
        raise RuntimeError(f"从 OSS 读取或解析文档失败：object_key={object_key}")

    chunks = chunk_text_by_sentence(text)
    if not chunks:
        # 空文档：无内容可索引，视为成功（避免留下 pending 状态）
        _finish_index_task(
            task_id, document_id, kb_id,
            {"chroma": True, "es": True, "chunk_count": 0, "note": "empty_content"},
            chunk_count=0,
        )
        return

    # 4. 向量化 + 双写（幂等）
    ingestion = IngestionService()
    ingest_result = ingestion.ingest_document(knowledge_base_id=kb_id, document_id=document_id, chunks=chunks)

    # 5. 依据结果更新状态
    if ingest_result["status"] == "success":
        _finish_index_task(
            task_id, document_id, kb_id,
            {
                "chroma": ingest_result["chroma_ok"],
                "es": ingest_result["es_ok"],
                "chunk_count": ingest_result["chunk_count"],
            },
            chunk_count=ingest_result["chunk_count"],
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
    处理单个删除任务：真实删除 Chroma/ES 索引，MySQL 记录逻辑删除，OSS 对象保留。
    任一步失败则抛异常由外层安排重试；已成功的索引删除操作幂等，重试无副作用。
    """
    # 1. 删除 Chroma + ES 索引（幂等）
    ingestion = IngestionService()
    delete_result = ingestion.delete_document(kb_id, document_id)
    failed_backends = [name for name, ok in delete_result.items() if not ok]
    if failed_backends:
        raise RuntimeError("文档索引删除失败，等待重试：" + ",".join(failed_backends))

    # 2. 逻辑删除 MySQL 记录（与任务完成状态一起提交）
    with get_connection() as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            cursor.execute("SELECT id FROM knowledge_base WHERE id = %s FOR UPDATE", (kb_id,))
            if cursor.fetchone() is None:
                return
            cursor.execute(
                "SELECT id FROM document WHERE id = %s AND knowledge_base_id = %s "
                "AND is_deleted = 0 AND status = 'deleting' FOR UPDATE",
                (document_id, kb_id),
            )
            if cursor.fetchone() is None:
                return
            cursor.execute(
                "SELECT id FROM document_task WHERE id = %s AND status = 'processing' "
                "AND claimed_by = %s FOR UPDATE",
                (task_id, WORKER_ID),
            )
            if cursor.fetchone() is None:
                return
            cursor.execute(
                "UPDATE document SET status = 'deleted', is_deleted = 1, deleted_at = NOW(), "
                "error_message = NULL, update_time = NOW() "
                "WHERE id = %s AND is_deleted = 0 AND status = 'deleting'",
                (document_id,)
            )
            cursor.execute(
                "UPDATE document_task SET status = 'done', result_json = %s, "
                "error_message = NULL, claimed_by = NULL, claimed_at = NULL, update_time = NOW() "
                "WHERE id = %s AND status = 'processing' AND claimed_by = %s",
                (
                    json.dumps(
                        {
                            "chroma": delete_result["chroma"],
                            "es": delete_result["es"],
                            "oss_retained": True,
                        },
                        ensure_ascii=False
                    ),
                    task_id, WORKER_ID,
                )
            )
            if cursor.rowcount != 1:
                raise RuntimeError("删除任务所有权已失效")
        finally:
            cursor.close()


def _handle_delete_kb_task(task_id: int, kb_id: int, payload: dict) -> None:
    """
    处理单个删除知识库任务：真实删除 Chroma/ES 索引，文档和知识库记录逻辑删除，OSS 对象保留。
    任一步失败则抛异常由外层安排重试；已成功的索引删除操作幂等，重试无副作用。
    """
    # 1. 删除 Chroma collection 与 ES 索引（幂等）
    ingestion = IngestionService()
    delete_result = ingestion.delete_knowledge_base(kb_id)
    failed_backends = [name for name, ok in delete_result.items() if not ok]
    if failed_backends:
        raise RuntimeError("知识库索引删除失败，等待重试：" + ",".join(failed_backends))

    # 2. 逻辑删除文档与知识库记录，并标记任务完成（单事务）
    with get_connection() as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            cursor.execute(
                "SELECT id FROM knowledge_base WHERE id = %s AND is_deleted = 1 FOR UPDATE",
                (kb_id,),
            )
            if cursor.fetchone() is None:
                return
            cursor.execute(
                "SELECT id FROM document_task WHERE id = %s AND status = 'processing' "
                "AND claimed_by = %s FOR UPDATE",
                (task_id, WORKER_ID),
            )
            if cursor.fetchone() is None:
                return
            cursor.execute(
                "UPDATE document SET status = 'deleted', is_deleted = 1, deleted_at = NOW(), "
                "error_message = NULL, update_time = NOW() "
                "WHERE knowledge_base_id = %s AND is_deleted = 0 AND status = 'deleting'",
                (kb_id,)
            )
            cursor.execute(
                "UPDATE knowledge_base SET is_deleted = 1, deleted_at = NOW() "
                "WHERE id = %s AND is_deleted = 1",
                (kb_id,)
            )
            cursor.execute(
                "UPDATE document_task SET status = 'done', result_json = %s, "
                "error_message = NULL, claimed_by = NULL, claimed_at = NULL, update_time = NOW() "
                "WHERE id = %s AND status = 'processing' AND claimed_by = %s",
                (
                    json.dumps(
                        {
                            "chroma": delete_result["chroma"],
                            "es": delete_result["es"],
                            "kb_id": kb_id,
                            "oss_retained": True,
                        },
                        ensure_ascii=False
                    ),
                    task_id, WORKER_ID,
                )
            )
            if cursor.rowcount != 1:
                raise RuntimeError("知识库删除任务所有权已失效")
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
                worker_id=WORKER_ID,
            )
            if final is None:
                print(f"[Worker] {task_type} task #{task.id} 已被其他 Worker 接管，跳过旧结果")
            elif task_type == "index":
                if final:
                    DocumentCRUD.update_status(task.document_id, "failed", error_message=str(e)[:2000])
                else:
                    # 仍在重试中，标记为 indexing（等待下次领取）
                    DocumentCRUD.update_status(task.document_id, "indexing", error_message=str(e)[:2000])
            elif task_type in ("delete", "delete_kb"):
                # 删除失败：相关文档保持 deleting，等待重试；超限后由人工排查。
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
