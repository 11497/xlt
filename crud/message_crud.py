from typing import List, Optional
from util.db_util import get_connection, get_cursor
from model.message_model import Message
from crud.message_source_crud import MessageSourceCRUD


class MessageCRUD:

    @staticmethod
    def create(message: Message) -> int:
        """
        新增消息
        :param message: 消息对象
        :return: 新插入记录的 id
        """
        sql = "INSERT INTO message (session_id, role, content, rewritten_content) VALUES (%s, %s, %s, %s)"
        with get_cursor() as cursor:
            cursor.execute(sql, (message.session_id, message.role, message.content, message.rewritten_content))
            return cursor.lastrowid

    @staticmethod
    def get_by_session_id(session_id: int) -> List[Message]:
        """
        根据会话 ID 查询对话消息列表，按创建时间升序排列
        :param session_id: 会话ID
        :return: 消息对象列表
        """
        sql = "SELECT * FROM message WHERE session_id = %s AND is_deleted = 0 ORDER BY create_time"
        with get_cursor() as cursor:
            cursor.execute(sql, (session_id,))
            rows = cursor.fetchall()
            return [Message.from_row(row) for row in rows]

    @staticmethod
    def delete_by_session_id(session_id: int) -> bool:
        """
        在同一事务中逻辑删除会话消息及其来源引用。
        :param session_id: 会话ID
        :return: 是否成功删除了记录
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            try:
                MessageSourceCRUD.soft_delete_by_session_id(cursor, session_id)
                cursor.execute(
                    "UPDATE message SET is_deleted = 1, deleted_at = NOW() "
                    "WHERE session_id = %s AND is_deleted = 0",
                    (session_id,)
                )
                return cursor.rowcount > 0
            finally:
                cursor.close()

    @staticmethod
    def delete_message_with_after(session_id: int, message_id: int) -> bool:
        """
        在同一事务中逻辑删除指定消息及之后的消息与来源引用。
        :param session_id: 会话ID
        :param message_id: 起始消息ID
        :return: 是否成功删除了记录
        """
        with get_connection() as conn:
            cursor = conn.cursor()
            try:
                MessageSourceCRUD.soft_delete_by_session_and_after(
                    cursor,
                    session_id,
                    message_id
                )
                cursor.execute(
                    "UPDATE message SET is_deleted = 1, deleted_at = NOW() "
                    "WHERE session_id = %s AND id >= %s AND is_deleted = 0",
                    (session_id, message_id)
                )
                return cursor.rowcount > 0
            finally:
                cursor.close()

    @staticmethod
    def get_by_id(message_id: int) -> Optional[Message]:
        """
        根据消息 ID 查询单个消息
        :param message_id: 消息ID
        :return: 消息对象（如果存在）
        """
        sql = "SELECT * FROM message WHERE id = %s AND is_deleted = 0"
        with get_cursor() as cursor:
            cursor.execute(sql, (message_id,))
            row = cursor.fetchone()
            return Message.from_row(row) if row else None

    @staticmethod
    def update_rewritten_content(message_id: int, rewritten_content: str) -> bool:
        """
        更新消息的重写后内容
        :param message_id: 消息ID
        :param rewritten_content: 重写后的内容
        :return: 是否成功更新
        """
        sql = "UPDATE message SET rewritten_content = %s WHERE id = %s AND is_deleted = 0"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, (rewritten_content, message_id))
            return affected > 0
