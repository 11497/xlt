from typing import List, Optional
from util.db_util import get_cursor
from model.session_model import Session
from datetime import datetime


class SessionCRUD:

    @staticmethod
    def create(session: Session) -> int:
        """
        新增会话
        :return: 新插入记录的 id
        """
        sql = "INSERT INTO session (user_id, name) VALUES (%s, %s)"
        with get_cursor() as cursor:
            cursor.execute(sql, (session.user_id, session.name))
            return cursor.lastrowid

    @staticmethod
    def get_by_id(session_id: int) -> Optional[Session]:
        """根据 ID 查询单个会话"""
        sql = "SELECT * FROM session WHERE id = %s"
        with get_cursor() as cursor:
            cursor.execute(sql, (session_id,))
            row = cursor.fetchone()
            return Session.from_row(row) if row else None

    @staticmethod
    def delete(session_id: int) -> bool:
        """
        根据 ID 删除会话
        :return: 是否成功删除了记录
        """
        sql = "DELETE FROM session WHERE id = %s"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, (session_id,))
            return affected > 0

    @staticmethod
    def get_by_user_id(user_id: int) -> List[Session]:
        """根据用户 ID 获取会话列表，按修改时间倒序排列"""
        sql = "SELECT * FROM session WHERE user_id = %s ORDER BY update_time DESC"
        with get_cursor() as cursor:
            cursor.execute(sql, (user_id,))
            rows = cursor.fetchall()
            return [Session.from_row(row) for row in rows]

    @staticmethod
    def update_session_name(session_id: int, name: str) -> bool:
        """
        更新会话名称
        :return: 是否成功更新了记录
        """
        sql = "UPDATE session SET name = %s WHERE id = %s"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, (name, session_id))
            return affected > 0

    @staticmethod
    def update_session_update_time(session_id: int) -> bool:
        """
        更新会话的修改时间为当前时间
        :return: 是否成功更新了记录
        """
        sql = "UPDATE session SET update_time = %s WHERE id = %s"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, (datetime.now(), session_id))
            return affected > 0

    @staticmethod
    def get_all() -> List[Session]:
        """
        获取所有会话
        :return: 所有会话列表
        """
        sql = "SELECT * FROM session"
        with get_cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [Session.from_row(row) for row in rows]
