from typing import List, Optional, Tuple
from util.db_util import get_cursor
from model.session_model import Session
from datetime import datetime


class SessionCRUD:

    @staticmethod
    def create(session: Session) -> int:
        """
        新增会话
        :param session: 会话对象
        :return: 新插入记录的 id
        """
        sql = "INSERT INTO session (user_id, name) VALUES (%s, %s)"
        with get_cursor() as cursor:
            cursor.execute(sql, (session.user_id, session.name))
            return cursor.lastrowid

    @staticmethod
    def get_by_id(session_id: int) -> Optional[Session]:
        """
        根据 ID 查询单个会话
        :param session_id: 会话ID
        :return: 会话对象（如果存在）
        """
        sql = "SELECT * FROM session WHERE id = %s"
        with get_cursor() as cursor:
            cursor.execute(sql, (session_id,))
            row = cursor.fetchone()
            return Session.from_row(row) if row else None

    @staticmethod
    def delete(session_id: int) -> bool:
        """
        根据 ID 删除会话
        :param session_id: 会话ID
        :return: 是否成功删除了记录
        """
        sql = "DELETE FROM session WHERE id = %s"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, (session_id,))
            return affected > 0

    @staticmethod
    def get_by_user_id(user_id: int) -> List[Session]:
        """
        根据用户 ID 获取会话列表，按修改时间倒序排列
        :param user_id: 用户ID
        :return: 会话对象列表
        """
        sql = "SELECT * FROM session WHERE user_id = %s ORDER BY update_time DESC"
        with get_cursor() as cursor:
            cursor.execute(sql, (user_id,))
            rows = cursor.fetchall()
            return [Session.from_row(row) for row in rows]

    @staticmethod
    def update_session_name(session_id: int, name: str) -> bool:
        """
        更新会话名称
        :param session_id: 会话ID
        :param name: 新的会话名
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
        :param session_id: 会话ID
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

    @staticmethod
    def get_page(page: int = 1, page_size: int = 10, user_id: Optional[int] = None) -> Tuple[List[Session], int]:
        """
        分页查询会话
        :param page: 页码（从1开始）
        :param page_size: 每页条数
        :param user_id: 用户ID（可选）
        :return: (会话列表, 总记录数)
        """
        offset = (page - 1) * page_size

        sql_count = "SELECT COUNT(*) FROM session"
        sql_data = "SELECT * FROM session LIMIT %s OFFSET %s"
        if user_id is not None:
            sql_count = "SELECT COUNT(*) AS total FROM session WHERE user_id = %s"
            sql_data = "SELECT * FROM session WHERE user_id = %s LIMIT %s OFFSET %s"

        with get_cursor() as cursor:
            # 获取总数，兼容字典游标和元组游标
            if user_id is not None:
                cursor.execute(sql_count, (user_id,))
            else:
                cursor.execute(sql_count)
            count_row = cursor.fetchone()
            if isinstance(count_row, dict):
                total = int(count_row.get("total", count_row.get("COUNT(*)", 0)))
            else:
                total = int(count_row[0]) if count_row else 0

            # 获取分页数据
            if user_id is not None:
                cursor.execute(sql_data, (user_id, page_size, offset))
            else:
                cursor.execute(sql_data, (page_size, offset))
            rows = cursor.fetchall()
            sessions = [Session.from_row(r) for r in rows]

        return sessions, total
