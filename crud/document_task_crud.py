import json
from datetime import datetime, timedelta
from typing import List, Optional

import pymysql

from util.db_util import get_connection
from model.document_task_model import DocumentTask


class DocumentTaskCRUD:

    @staticmethod
    def create(task: DocumentTask) -> int:
        """
        新增任务（默认状态 pending）
        :param task: 任务对象
        :return: 新插入记录的 id
        """
        sql = ("INSERT INTO document_task "
               "(task_type, document_id, knowledge_base_id, status, payload, max_retries) "
               "VALUES (%s, %s, %s, %s, %s, %s)")
        with get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            try:
                cursor.execute(sql, (
                    task.task_type,
                    task.document_id,
                    task.knowledge_base_id,
                    "pending",
                    task.payload,
                    task.max_retries
                ))
                return cursor.lastrowid
            finally:
                cursor.close()

    @staticmethod
    def get_by_id(task_id: int) -> Optional[DocumentTask]:
        """根据 ID 查询任务"""
        sql = "SELECT * FROM document_task WHERE id = %s"
        with get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            try:
                cursor.execute(sql, (task_id,))
                row = cursor.fetchone()
                return DocumentTask.from_row(row) if row else None
            finally:
                cursor.close()

    @staticmethod
    def get_by_document_id(document_id: int, task_type: Optional[str] = None) -> List[DocumentTask]:
        """
        根据文档 ID 查询任务
        :param document_id: 文档ID
        :param task_type: 任务类型（可选，index/delete）
        :return: 任务对象列表
        """
        if task_type:
            sql = "SELECT * FROM document_task WHERE document_id = %s AND task_type = %s ORDER BY id DESC"
            params = (document_id, task_type)
        else:
            sql = "SELECT * FROM document_task WHERE document_id = %s ORDER BY id DESC"
            params = (document_id,)
        with get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            try:
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                return [DocumentTask.from_row(r) for r in rows]
            finally:
                cursor.close()

    @staticmethod
    def get_pending_tasks(task_type: Optional[str] = None, limit: int = 20) -> List[DocumentTask]:
        """
        查询待处理任务（pending 且已到重试时间）
        :param task_type: 任务类型（可选）
        :param limit: 数量上限
        :return: 任务对象列表
        """
        if task_type:
            sql = ("SELECT * FROM document_task WHERE task_type = %s AND status = 'pending' "
                   "AND (next_retry_at IS NULL OR next_retry_at <= NOW()) ORDER BY id ASC LIMIT %s")
            params = (task_type, limit)
        else:
            sql = ("SELECT * FROM document_task WHERE status = 'pending' "
                   "AND (next_retry_at IS NULL OR next_retry_at <= NOW()) ORDER BY id ASC LIMIT %s")
            params = (limit,)
        with get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            try:
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                return [DocumentTask.from_row(r) for r in rows]
            finally:
                cursor.close()

    @staticmethod
    def get_stuck_processing_tasks(timeout_minutes: int = 15, limit: int = 100) -> List[DocumentTask]:
        """
        查询长时间停留在 processing 的任务（疑似进程崩溃）
        :param timeout_minutes: 超时分钟数
        :param limit: 数量上限
        :return: 任务对象列表
        """
        sql = ("SELECT * FROM document_task WHERE status = 'processing' "
               "AND update_time < NOW() - INTERVAL %s MINUTE ORDER BY id ASC LIMIT %s")
        with get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            try:
                cursor.execute(sql, (timeout_minutes, limit))
                rows = cursor.fetchall()
                return [DocumentTask.from_row(r) for r in rows]
            finally:
                cursor.close()

    @staticmethod
    def get_failed_tasks(task_type: Optional[str] = None, limit: int = 100) -> List[DocumentTask]:
        """
        查询失败任务
        :param task_type: 任务类型（可选）
        :param limit: 数量上限
        :return: 任务对象列表
        """
        if task_type:
            sql = "SELECT * FROM document_task WHERE task_type = %s AND status = 'failed' ORDER BY id ASC LIMIT %s"
            params = (task_type, limit)
        else:
            sql = "SELECT * FROM document_task WHERE status = 'failed' ORDER BY id ASC LIMIT %s"
            params = (limit,)
        with get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            try:
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                return [DocumentTask.from_row(r) for r in rows]
            finally:
                cursor.close()

    @staticmethod
    def claim_next(task_type: str, worker_id: str, limit: int = 1) -> List[DocumentTask]:
        """
        原子领取任务：将 pending 且已到重试时间的任务置为 processing
        使用 FOR UPDATE SKIP LOCKED 避免并发 Worker 重复领取
        :param task_type: 任务类型
        :param worker_id: Worker 标识（记录到 error_message 便于排查）
        :param limit: 领取数量
        :return: 领取到的任务对象列表
        """
        claimed: List[DocumentTask] = []
        with get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            try:
                cursor.execute(
                    "SELECT * FROM document_task "
                    "WHERE task_type = %s AND status = 'pending' "
                    "AND (next_retry_at IS NULL OR next_retry_at <= NOW()) "
                    "ORDER BY id ASC LIMIT %s FOR UPDATE SKIP LOCKED",
                    (task_type, limit)
                )
                rows = cursor.fetchall()
                for row in rows:
                    cursor.execute(
                        "UPDATE document_task SET status = 'processing', "
                        "error_message = %s, update_time = NOW() WHERE id = %s",
                        (f"claimed by {worker_id}", row["id"])
                    )
                    claimed.append(DocumentTask.from_row(row))
            finally:
                cursor.close()
        return claimed

    @staticmethod
    def mark_done(task_id: int, result_json: Optional[dict] = None) -> bool:
        """
        标记任务完成
        :param task_id: 任务ID
        :param result_json: 各存储执行结果
        :return: 是否更新成功
        """
        if result_json is not None:
            sql = ("UPDATE document_task SET status = 'done', error_message = NULL, "
                   "result_json = %s, update_time = NOW() WHERE id = %s")
            params = (json.dumps(result_json, ensure_ascii=False), task_id)
        else:
            sql = "UPDATE document_task SET status = 'done', error_message = NULL, update_time = NOW() WHERE id = %s"
            params = (task_id,)
        with get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            try:
                affected = cursor.execute(sql, params)
                return affected > 0
            finally:
                cursor.close()

    @staticmethod
    def mark_retry(task_id: int, error_message: str, retry_count: int, max_retries: int) -> bool:
        """
        任务失败，按指数退避安排重试；超过最大次数则标记 failed
        :param task_id: 任务ID
        :param error_message: 失败原因
        :param retry_count: 当前已重试次数（含本次）
        :param max_retries: 最大重试次数
        :return: 是否标记为最终失败（True=failed，False=已安排重试）
        """
        if retry_count >= max_retries:
            sql = ("UPDATE document_task SET status = 'failed', error_message = %s, "
                   "retry_count = %s, update_time = NOW() WHERE id = %s")
            params = (error_message[:2000], retry_count, task_id)
            is_final = True
        else:
            # 指数退避：1m, 5m, 30m, 2h, 8h...
            delay_seconds = min(30 * (2 ** (retry_count - 1)), 8 * 3600)
            next_retry = datetime.now() + timedelta(seconds=delay_seconds)
            sql = ("UPDATE document_task SET status = 'pending', error_message = %s, "
                   "retry_count = %s, next_retry_at = %s, update_time = NOW() WHERE id = %s")
            params = (error_message[:2000], retry_count, next_retry, task_id)
            is_final = False
        with get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            try:
                cursor.execute(sql, params)
                return is_final
            finally:
                cursor.close()

    @staticmethod
    def reset_stuck_tasks(task_ids: List[int], worker_id: str = "reconciliation") -> int:
        """
        将卡死的 processing 任务重置为 pending
        :param task_ids: 任务ID列表
        :param worker_id: 操作标识
        :return: 重置的任务数量
        """
        if not task_ids:
            return 0
        placeholders = ",".join(["%s"] * len(task_ids))
        sql = (f"UPDATE document_task SET status = 'pending', error_message = %s, "
               f"update_time = NOW() WHERE id IN ({placeholders})")
        with get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            try:
                affected = cursor.execute(sql, (f"reset by {worker_id}", *task_ids))
                return affected
            finally:
                cursor.close()

    @staticmethod
    def get_tasks_by_knowledge_base(knowledge_base_id: int, task_type: Optional[str] = None) -> List[DocumentTask]:
        """
        按知识库查询任务（删除知识库时对账用）
        :param knowledge_base_id: 知识库ID
        :param task_type: 任务类型（可选）
        :return: 任务对象列表
        """
        if task_type:
            sql = ("SELECT * FROM document_task WHERE knowledge_base_id = %s AND task_type = %s "
                   "ORDER BY id ASC")
            params = (knowledge_base_id, task_type)
        else:
            sql = "SELECT * FROM document_task WHERE knowledge_base_id = %s ORDER BY id ASC"
            params = (knowledge_base_id,)
        with get_connection() as conn:
            cursor = conn.cursor(pymysql.cursors.DictCursor)
            try:
                cursor.execute(sql, params)
                rows = cursor.fetchall()
                return [DocumentTask.from_row(r) for r in rows]
            finally:
                cursor.close()
