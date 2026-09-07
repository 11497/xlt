"""将超限失败的 document_task 重置为可再次领取。

Elasticsearch / Chroma 恢复后运行，让独立 Worker 幂等重试索引或删除。
对账服务不会自动重开 failed 的 delete / delete_kb，因此需要本脚本人工复位。

用法：
  uv run python scripts/reset_failed_document_tasks.py
  uv run python scripts/reset_failed_document_tasks.py --dry-run
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import config  # noqa: E402

import pymysql  # noqa: E402

from util.db_util import get_connection  # noqa: E402

TASK_TYPES = ("index", "delete", "delete_kb")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="将 failed 的文档任务重置为 pending，供 Worker 重新执行")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印将要复位的任务，不写库",
    )
    parser.add_argument(
        "--task-type",
        choices=TASK_TYPES,
        action="append",
        dest="task_types",
        help="只复位指定类型，可重复传入；默认全部类型",
    )
    return parser.parse_args()


def _format_task(row: dict) -> str:
    return (
        f"id={row['id']} type={row['task_type']} "
        f"doc={row['document_id']} kb={row['knowledge_base_id']} "
        f"retry={row['retry_count']}/{row['max_retries']} "
        f"error={row['error_message']}"
    )


def reset_failed_tasks(task_types: tuple[str, ...], dry_run: bool) -> int:
    placeholders = ",".join(["%s"] * len(task_types))
    select_sql = (
        "SELECT id, task_type, document_id, knowledge_base_id, retry_count, "
        "max_retries, error_message FROM document_task "
        f"WHERE status = 'failed' AND task_type IN ({placeholders}) "
        "ORDER BY id ASC FOR UPDATE"
    )
    with get_connection() as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            cursor.execute(select_sql, task_types)
            rows = list(cursor.fetchall())
            if not rows:
                print("没有需要复位的 failed 任务")
                return 0

            print(f"找到 {len(rows)} 条 failed 任务：")
            for row in rows:
                print("  " + _format_task(row))

            if dry_run:
                print("dry-run：未写库")
                return 0

            task_ids = [row["id"] for row in rows]
            id_placeholders = ",".join(["%s"] * len(task_ids))
            cursor.execute(
                "UPDATE document_task SET status = 'pending', retry_count = 0, "
                "next_retry_at = NULL, error_message = NULL, result_json = NULL, "
                "claimed_by = NULL, claimed_at = NULL, update_time = NOW() "
                f"WHERE status = 'failed' AND id IN ({id_placeholders})",
                task_ids,
            )
            reset_tasks = cursor.rowcount

            index_doc_ids = sorted({
                row["document_id"]
                for row in rows
                if row["task_type"] == "index" and row["document_id"]
            })
            reset_docs = 0
            if index_doc_ids:
                doc_placeholders = ",".join(["%s"] * len(index_doc_ids))
                cursor.execute(
                    "UPDATE document SET status = 'pending', error_message = NULL, "
                    "update_time = NOW() "
                    f"WHERE is_deleted = 0 AND status = 'failed' "
                    f"AND id IN ({doc_placeholders})",
                    index_doc_ids,
                )
                reset_docs = cursor.rowcount

            print(
                f"已复位任务 {reset_tasks} 条；"
                f"将 failed 文档改回 pending {reset_docs} 条。"
                "请确认 Worker 正在运行。"
            )
            return reset_tasks
        finally:
            cursor.close()


def main() -> None:
    args = parse_args()
    task_types = tuple(args.task_types) if args.task_types else TASK_TYPES
    reset_failed_tasks(task_types, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
