"""文档索引对账服务（定期执行，幂等、只补不删）。

独立进程运行：uv run python -m ai.reconciliation_service
负责：
1. 恢复卡死的 processing 任务（Worker 进程崩溃后遗留）
2. 将 failed 但未超过重试上限的任务重新入队
3. 核对 ready 文档在 Chroma/ES 的实际切片数与记录是否一致，不一致则补索引
4. 报告 OSS 中不在 document 表内的对象；按逻辑删除约定，对账服务不删除任何对象
"""
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, List, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv  # noqa: E402
load_dotenv(PROJECT_ROOT / ".env")

import pymysql  # noqa: E402

from ai.es_service import ESService  # noqa: E402
from ai.chroma_service import ChromaService  # noqa: E402
from crud.document_crud import DocumentCRUD  # noqa: E402
from crud.document_task_crud import DocumentTaskCRUD  # noqa: E402
from model.document_task_model import DocumentTask  # noqa: E402
from util.db_util import get_connection  # noqa: E402

POLL_INTERVAL = int(os.getenv("RECONCILE_INTERVAL", "600"))  # 秒，默认 10 分钟
STUCK_TIMEOUT_MINUTES = int(os.getenv("RECONCILE_STUCK_TIMEOUT", "15"))
OSS_PREFIX = "knowledge_base/"


def _recover_stuck_tasks() -> int:
    """将卡死的 processing 任务重置为 pending"""
    stuck = DocumentTaskCRUD.get_stuck_processing_tasks(timeout_minutes=STUCK_TIMEOUT_MINUTES)
    if not stuck:
        return 0
    task_ids = [t.id for t in stuck]
    count = DocumentTaskCRUD.reset_stuck_tasks(
        task_ids, timeout_minutes=STUCK_TIMEOUT_MINUTES
    )
    print(f"[Reconcile] 恢复卡死任务 {count} 个：{task_ids}")
    return count


def _recover_retryable_failed_tasks() -> int:
    """
    将 failed 但 retry_count < max_retries 的索引任务重置为 pending（下次轮询会领取重试）。
    删除任务失败不自动转回索引重试，避免覆盖删除语义。
    """
    failed = DocumentTaskCRUD.get_failed_tasks(task_type="index")
    reset_ids = []
    for task in failed:
        if task.retry_count < task.max_retries:
            with get_connection() as conn:
                cursor = conn.cursor()
                try:
                    cursor.execute(
                        "UPDATE document_task SET status = 'pending', next_retry_at = NULL, "
                        "error_message = NULL, claimed_by = NULL, claimed_at = NULL, update_time = NOW() "
                        "WHERE id = %s AND status = 'failed' AND retry_count < max_retries",
                        (task.id,)
                    )
                finally:
                    cursor.close()
            reset_ids.append(task.id)
    if reset_ids:
        print(f"[Reconcile] 重新入队可重试失败任务 {len(reset_ids)} 个：{reset_ids}")
    return len(reset_ids)


def _find_index_tasks(document_id: int) -> List[DocumentTask]:
    """查询某文档所有索引任务"""
    return DocumentTaskCRUD.get_by_document_id(document_id, task_type="index")


def _enqueue_reindex_if_still_active(doc: Any, payload: str) -> bool:
    """在知识库锁内再次确认文档可索引，并原子地补入任务。"""
    with get_connection() as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            cursor.execute(
                "SELECT id FROM knowledge_base WHERE id = %s AND is_deleted = 0 FOR UPDATE",
                (doc.knowledge_base_id,),
            )
            if cursor.fetchone() is None:
                return False
            cursor.execute(
                "SELECT id FROM document WHERE id = %s AND knowledge_base_id = %s "
                "AND is_deleted = 0 AND status = 'ready' FOR UPDATE",
                (doc.id, doc.knowledge_base_id),
            )
            if cursor.fetchone() is None:
                return False
            cursor.execute(
                "SELECT id FROM document_task WHERE document_id = %s AND task_type = 'index' "
                "AND status IN ('pending', 'processing') FOR UPDATE",
                (doc.id,),
            )
            if cursor.fetchone() is not None:
                return False
            cursor.execute(
                "INSERT INTO document_task "
                "(task_type, document_id, knowledge_base_id, status, payload) "
                "VALUES ('index', %s, %s, 'pending', %s)",
                (doc.id, doc.knowledge_base_id, payload),
            )
            cursor.execute(
                "UPDATE document SET status = 'pending', update_time = NOW() "
                "WHERE id = %s AND is_deleted = 0 AND status = 'ready'",
                (doc.id,),
            )
            return cursor.rowcount == 1
        finally:
            cursor.close()


def _check_and_fix_index_consistency() -> int:
    """
    核对 ready 文档的 Chroma/ES 切片数，与 document.chunk_count 不一致则重新入队索引。
    :return: 需要补索引的文档数量
    """
    # 只对账未逻辑删除的 ready 文档；已删除索引不能被自动补回。
    ready_docs = DocumentCRUD.get_by_status("ready", limit=200)
    chroma = ChromaService()
    es = ESService()
    fixed = 0
    for doc in ready_docs:
        # ready 不应是删除中状态；防御性跳过，避免并发删除后补写索引。
        if doc.status == "deleting":
            continue

        # 存在进行中/待处理任务则跳过（避免重复）
        tasks = _find_index_tasks(doc.id)
        if tasks and any(t.status in ("pending", "processing") for t in tasks):
            continue

        chroma_count = chroma.get_document_chunk_count(doc.knowledge_base_id, doc.id)
        es_count = es.get_document_chunk_count(doc.knowledge_base_id, doc.id)
        expected = doc.chunk_count or 0

        # 某端查询失败返回 -1，视为待确认，跳过本次
        if chroma_count < 0 or es_count < 0:
            print(f"[Reconcile] doc={doc.id} 端查询失败（chroma={chroma_count}, es={es_count}），跳过")
            continue

        if chroma_count != expected or es_count != expected:
            # 补索引：入队新任务（幂等 upsert 会覆盖补齐）
            payload = json.dumps(
                {"object_key": doc.storage_path, "filename": doc.filename}, ensure_ascii=False
            )
            if not _enqueue_reindex_if_still_active(doc, payload):
                continue
            print(
                f"[Reconcile] doc={doc.id} 索引不一致：chroma={chroma_count}, es={es_count}, "
                f"expected={expected}，已重新入队"
            )
            fixed += 1
    return fixed


def _report_orphan_oss() -> int:
    """
    保留 OSS 对象，不提供孤儿对象枚举。

    OSS 是留存层，当前对账服务没有列举权限和删除职责；返回值固定为 0
    表示本轮没有执行 OSS 清理，而不是表示 OSS 中不存在孤儿对象。
    """
    return 0


def run_once() -> dict:
    """执行一轮对账，返回各项处理数量"""
    stuck = _recover_stuck_tasks()
    retryable = _recover_retryable_failed_tasks()
    fixed = _check_and_fix_index_consistency()
    _report_orphan_oss()
    summary = {
        "stuck_recovered": stuck,
        "retryable_requeued": retryable,
        "index_fixed": fixed,
        "oss_objects_deleted": 0,
    }
    print(f"[Reconcile] 本轮完成：{summary}")
    return summary


def main_loop() -> None:
    print(f"[Reconcile] 对账服务启动，每 {POLL_INTERVAL}s 执行一轮")
    while True:
        try:
            run_once()
        except KeyboardInterrupt:
            print("[Reconcile] 收到中断，退出")
            break
        except Exception as e:
            print(f"[Reconcile] 对账异常：{e}")
        time.sleep(POLL_INTERVAL)


if __name__ == "__main__":
    main_loop()
