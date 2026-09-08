"""人工恢复单个已删除文档的检索索引。

本脚本不会创建 document_task，也不会删除或覆盖 OSS 原始对象。
默认仅执行数据库检查；必须显式传入 --execute 才会访问 OSS、模型和检索服务。
"""
from __future__ import annotations

import argparse
import asyncio
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config  # noqa: E402
import pymysql  # noqa: E402

from ai.ingestion_service import IngestionService  # noqa: E402
from util.db_util import get_connection  # noqa: E402
from util.file_util import chunk_text_by_sentence, read_file_content  # noqa: E402
from util.oss_util import OSSUtil  # noqa: E402

# !!! 执行前必须把此 ID 修改为需要人工恢复的已删除文档 ID，严禁保留默认值执行。!!!
DOCUMENT_ID = 2


@dataclass(frozen=True)
class RestoreTarget:
    document_id: int
    knowledge_base_id: int
    filename: str
    storage_path: str
    status: str
    chunk_count: Optional[int]


class RestoreBlockedError(RuntimeError):
    """前置条件不满足，不能执行恢复。"""


def _ensure_no_active_tasks(cursor, target: RestoreTarget, *, for_update: bool = False) -> None:
    """确认没有会与人工恢复并发操作索引的活动任务。"""
    lock_clause = " FOR UPDATE" if for_update else ""
    cursor.execute(
        "SELECT id, task_type, status FROM document_task "
        "WHERE document_id = %s AND status IN ('pending', 'processing') LIMIT 1" + lock_clause,
        (target.document_id,),
    )
    task = cursor.fetchone()
    if task is not None:
        raise RestoreBlockedError(
            f"文档存在活动任务（id={task['id']}，type={task['task_type']}，status={task['status']}）"
        )

    cursor.execute(
        "SELECT id, task_type, status FROM document_task "
        "WHERE knowledge_base_id = %s AND task_type = 'delete_kb' "
        "AND status IN ('pending', 'processing') LIMIT 1" + lock_clause,
        (target.knowledge_base_id,),
    )
    task = cursor.fetchone()
    if task is not None:
        raise RestoreBlockedError(
            f"知识库存在活动删除任务（id={task['id']}，status={task['status']}）"
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="人工恢复单个已删除文档的 ChromaDB 与 Elasticsearch 索引")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="确认执行恢复；未提供时仅进行只读检查和 dry-run",
    )
    return parser.parse_args()


def restore_uploaded_filename(object_key: str, expected_filename: str) -> str:
    """只识别上传路由生成的 ``uuid4().hex + '_' + 原始文件名`` 格式。

    文件名字段是权威的原始展示名。只有对象 basename 的 UUID 前缀之后严格等于该
    字段时才去除前缀，避免把用户正常文件名中的内容误当作 UUID 删除。
    """
    object_name = PurePosixPath(object_key).name
    prefix_length = 32
    if (
        len(object_name) > prefix_length + 1
        and object_name[prefix_length] == "_"
        and all(char in "0123456789abcdef" for char in object_name[:prefix_length].lower())
        and object_name[prefix_length + 1:] == expected_filename
    ):
        return object_name[prefix_length + 1:]
    return expected_filename


def _safe_temp_filename(filename: str) -> str:
    """将历史记录中的文件名限制为临时目录内的 basename。"""
    safe_name = PurePosixPath(filename.replace("\\", "/")).name
    if safe_name in ("", ".", ".."):
        raise RestoreBlockedError("文档文件名不适合写入临时目录")
    return safe_name


def load_restore_target(document_id: int) -> RestoreTarget:
    """读取已删除文档及其知识库，并严格校验恢复前置条件。"""
    with get_connection() as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            cursor.execute(
                "SELECT id, knowledge_base_id, filename, storage_path, status, chunk_count, is_deleted "
                "FROM document WHERE id = %s",
                (document_id,),
            )
            document = cursor.fetchone()
            if document is None:
                raise RestoreBlockedError(f"文档 ID={document_id} 不存在")
            if document["is_deleted"] != 1 or document["status"] != "deleted":
                raise RestoreBlockedError(
                    f"文档 ID={document_id} 当前不是已删除状态（is_deleted={document['is_deleted']}，"
                    f"status={document['status']}）"
                )
            if not document["storage_path"] or not str(document["storage_path"]).strip():
                raise RestoreBlockedError("文档未保留可用的 OSS 对象定位信息 storage_path")

            cursor.execute(
                "SELECT id, is_deleted FROM knowledge_base WHERE id = %s",
                (document["knowledge_base_id"],),
            )
            knowledge_base = cursor.fetchone()
            if knowledge_base is None:
                raise RestoreBlockedError(f"所属知识库 ID={document['knowledge_base_id']} 不存在")
            if knowledge_base["is_deleted"] != 0:
                raise RestoreBlockedError(f"所属知识库 ID={document['knowledge_base_id']} 已删除")
            target = RestoreTarget(
                document_id=document["id"],
                knowledge_base_id=document["knowledge_base_id"],
                filename=document["filename"],
                storage_path=document["storage_path"],
                status=document["status"],
                chunk_count=document["chunk_count"],
            )
            _ensure_no_active_tasks(cursor, target)
            return target
        finally:
            cursor.close()


def print_summary(target: RestoreTarget) -> None:
    parser_filename = restore_uploaded_filename(target.storage_path, target.filename)
    print("恢复目标摘要：")
    print(f"  文档：ID={target.document_id}，文件名={target.filename}，当前状态={target.status}")
    print(f"  知识库：ID={target.knowledge_base_id}")
    print(f"  OSS 对象：{target.storage_path}")
    print(f"  解析文件名：{parser_filename}")
    print(f"  目标索引：ChromaDB collection=knowledge_base_{target.knowledge_base_id}；ES index=kb_{target.knowledge_base_id}")
    print("  活动任务检查：通过（文档无活动任务，知识库无活动 delete_kb 任务）")


class _TemporaryUploadFile:
    """为现有 read_file_content 提供最小 UploadFile 兼容接口。"""

    def __init__(self, path: Path, filename: str):
        self.path = path
        self.filename = filename

    async def read(self, _size: int = -1) -> bytes:
        return self.path.read_bytes()


async def download_to_tempfile(target: RestoreTarget, directory: Path) -> Path:
    """下载 OSS 对象到本次专属临时目录，不对 OSS 执行任何写操作。"""
    async with OSSUtil() as oss_client:
        result = await oss_client.get_file(target.storage_path)
    if not result.get("exists"):
        raise RestoreBlockedError(f"OSS 对象不存在：{target.storage_path}")
    local_path = directory / _safe_temp_filename(
        restore_uploaded_filename(target.storage_path, target.filename)
    )
    local_path.write_bytes(result["content"])
    return local_path


async def parse_chunks(target: RestoreTarget, directory: Path) -> list[str]:
    local_path = await download_to_tempfile(target, directory)
    text = await read_file_content(
        _TemporaryUploadFile(local_path, restore_uploaded_filename(target.storage_path, target.filename))
    )
    if text is None:
        raise RuntimeError("文档解析失败：文件类型不受支持或内容无法读取")
    return chunk_text_by_sentence(text)


def _cleanup_document_indexes(target: RestoreTarget, ingestion: IngestionService) -> bool:
    result = ingestion.delete_document(target.knowledge_base_id, target.document_id)
    chroma_ok = result["chroma"]
    es_ok = result["es"]
    if chroma_ok and es_ok:
        return True
    print(f"错误：清理旧切片失败（Chroma={chroma_ok}，Elasticsearch={es_ok}）。")
    print("请人工核对并清理当前文档的残留索引后再重试。")
    return False


def restore_indexes(target: RestoreTarget, chunks: list[str], ingestion: IngestionService) -> bool:
    """删除当前文档旧切片后重建双端索引，并在部分成功时补偿。"""
    if not _cleanup_document_indexes(target, ingestion):
        return False
    if not chunks:
        return True

    try:
        result = ingestion.ingest_document(target.knowledge_base_id, target.document_id, chunks)
    except Exception as exc:
        print(f"错误：索引写入异常：{exc}")
        _cleanup_document_indexes(target, ingestion)
        return False

    if result.get("status") == "success":
        return True

    print(
        f"索引恢复失败（status={result.get('status')}，Chroma={result.get('chroma_ok')}，"
        f"Elasticsearch={result.get('es_ok')}），正在补偿本次写入。"
    )
    compensation_ok = _cleanup_document_indexes(target, ingestion)
    print(f"补偿结果：双端清理={'成功' if compensation_ok else '未完全成功'}。")
    print("数据库仍保持已删除状态，OSS 原始文件未修改。请处理故障后重新执行本脚本。")
    return False


def mark_document_ready(target: RestoreTarget, chunk_count: int) -> bool:
    """仅在双端索引完成后恢复数据库业务状态，不创建或修改 document_task。"""
    with get_connection() as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            cursor.execute(
                "SELECT id FROM knowledge_base WHERE id = %s AND is_deleted = 0 FOR UPDATE",
                (target.knowledge_base_id,),
            )
            if cursor.fetchone() is None:
                raise RestoreBlockedError("最终落库前发现知识库不存在或已删除")
            cursor.execute(
                "SELECT id FROM document WHERE id = %s AND knowledge_base_id = %s "
                "AND is_deleted = 1 AND status = 'deleted' FOR UPDATE",
                (target.document_id, target.knowledge_base_id),
            )
            if cursor.fetchone() is None:
                raise RestoreBlockedError("最终落库前发现文档状态已变化，拒绝覆盖")
            _ensure_no_active_tasks(cursor, target, for_update=True)
            cursor.execute(
                "UPDATE document SET is_deleted = 0, deleted_at = NULL, status = 'ready', "
                "error_message = NULL, retry_count = 0, chunk_count = %s, update_time = NOW() "
                "WHERE id = %s AND knowledge_base_id = %s AND is_deleted = 1 AND status = 'deleted'",
                (chunk_count, target.document_id, target.knowledge_base_id),
            )
            if cursor.rowcount != 1:
                raise RestoreBlockedError("恢复文档状态失败：记录已被并发修改")
            return True
        finally:
            cursor.close()


def execute_restore(target: RestoreTarget) -> bool:
    """执行恢复并保证临时文件始终清理。"""
    with tempfile.TemporaryDirectory(prefix="xlt_restore_deleted_document_") as temp_dir:
        chunks = asyncio.run(parse_chunks(target, Path(temp_dir)))
        ingestion = IngestionService()
        if not restore_indexes(target, chunks, ingestion):
            return False
        try:
            mark_document_ready(target, len(chunks))
        except Exception as exc:
            print(f"错误：双端索引已恢复，但数据库最终状态更新失败：{exc}")
            print("正在补偿删除本次恢复的当前文档索引，避免数据库已删除而索引可检索。")
            compensation_ok = _cleanup_document_indexes(target, ingestion)
            print(f"数据库失败补偿结果：双端清理={'成功' if compensation_ok else '未完全成功'}。")
            if not compensation_ok:
                print("警告：补偿未完全成功。数据库仍为已删除，请立即人工清理当前文档索引。")
            return False
    return True


def main() -> int:
    args = parse_args()
    if DOCUMENT_ID <= 0:
        print("错误：请先在脚本顶部将 DOCUMENT_ID 修改为正整数文档 ID。")
        return 2
    try:
        target = load_restore_target(DOCUMENT_ID)
    except RestoreBlockedError as exc:
        print(f"检查未通过：{exc}")
        return 2
    except Exception as exc:
        print(f"检查失败：无法读取数据库记录：{exc}")
        return 1

    print_summary(target)
    if not args.execute:
        print("dry-run：未下载 OSS 文件，未修改 MySQL、ChromaDB 或 Elasticsearch。传入 --execute 才会执行恢复。")
        return 0
    try:
        if not execute_restore(target):
            return 1
    except RestoreBlockedError as exc:
        print(f"恢复未执行：{exc}")
        return 2
    except Exception as exc:
        print(f"恢复失败：{exc}")
        return 1
    print(f"恢复成功：文档 ID={target.document_id} 已恢复为 ready，ChromaDB 与 Elasticsearch 索引已重建。")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
