from typing import List, Optional
from util.db_util import get_cursor
from model.message_model import Message


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
        sql = "SELECT * FROM message WHERE session_id = %s ORDER BY create_time"
        with get_cursor() as cursor:
            cursor.execute(sql, (session_id,))
            rows = cursor.fetchall()
            return [Message.from_row(row) for row in rows]

    @staticmethod
    def delete_by_session_id(session_id: int) -> bool:
        """
        根据会话 ID 删除该会话下的所有消息
        :param session_id: 会话ID
        :return: 是否成功删除了记录
        """
        sql = "DELETE FROM message WHERE session_id = %s"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, (session_id,))
            return affected > 0

    @staticmethod
    def delete_message_with_after(session_id: int, message_id: int) -> bool:
        """
        根据会话 ID 和消息 ID，删除该会话内该消息 ID 之后的所有消息
        :param session_id: 会话ID
        :param message_id: 消息ID
        :return: 是否成功删除了记录
        """
        sql = "DELETE FROM message WHERE session_id = %s AND id >= %s"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, (session_id, message_id))
            return affected > 0

    @staticmethod
    def get_by_id(message_id: int) -> Optional[Message]:
        """
        根据消息 ID 查询单个消息
        :param message_id: 消息ID
        :return: 消息对象（如果存在）
        """
        sql = "SELECT * FROM message WHERE id = %s"
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
        sql = "UPDATE message SET rewritten_content = %s WHERE id = %s"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, (rewritten_content, message_id))
            return affected > 0