from typing import List, Optional
from db.db_connection import get_cursor
from model.announcement_attachment_model import AnnouncementAttachment


class AnnouncementAttachmentCRUD:

    @staticmethod
    def create(attachment: AnnouncementAttachment) -> int:
        """
        新增公告附件
        :return: 新插入记录的 id
        """
        sql = "INSERT INTO announcement_attachment (announcement_id, filename, storage_path) VALUES (%s, %s, %s)"
        with get_cursor() as cursor:
            cursor.execute(sql, (attachment.announcement_id, attachment.filename, attachment.storage_path))
            return cursor.lastrowid

    @staticmethod
    def get_by_id(attachment_id: int) -> Optional[AnnouncementAttachment]:
        """根据 ID 查询单个公告附件"""
        sql = "SELECT * FROM announcement_attachment WHERE id = %s"
        with get_cursor() as cursor:
            cursor.execute(sql, (attachment_id,))
            row = cursor.fetchone()
            return AnnouncementAttachment.from_row(row) if row else None

    @staticmethod
    def get_by_announcement_id(announcement_id: int) -> List[AnnouncementAttachment]:
        """根据公告 ID 查询所有附件"""
        sql = "SELECT * FROM announcement_attachment WHERE announcement_id = %s ORDER BY upload_time DESC"
        with get_cursor() as cursor:
            cursor.execute(sql, (announcement_id,))
            rows = cursor.fetchall()
            return [AnnouncementAttachment.from_row(r) for r in rows]

    @staticmethod
    def get_all() -> List[AnnouncementAttachment]:
        """查询所有公告附件"""
        sql = "SELECT * FROM announcement_attachment ORDER BY upload_time DESC"
        with get_cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [AnnouncementAttachment.from_row(r) for r in rows]

    @staticmethod
    def update_filename(attachment_id: int, filename: str) -> bool:
        """
        根据 ID 更新附件文件名
        :return: 是否成功更新了记录
        """
        if attachment_id is None:
            raise ValueError("更新操作需要提供 attachment_id")
        sql = "UPDATE announcement_attachment SET filename = %s WHERE id = %s"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, (filename, attachment_id))
            return affected > 0

    @staticmethod
    def delete(attachment_id: int) -> bool:
        """
        根据 ID 删除公告附件
        :return: 是否成功删除了记录
        """
        sql = "DELETE FROM announcement_attachment WHERE id = %s"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, (attachment_id,))
            return affected > 0

    @staticmethod
    def batch_delete(attachment_ids: List[int]) -> int:
        """
        批量删除公告附件
        :param attachment_ids: 要删除的附件ID列表
        :return: 成功删除的记录数量
        """
        if not attachment_ids:
            return 0

        placeholders = ','.join(['%s'] * len(attachment_ids))
        sql = f"DELETE FROM announcement_attachment WHERE id IN ({placeholders})"
        with get_cursor() as cursor:
            cursor.execute(sql, attachment_ids)
            return cursor.rowcount

    @staticmethod
    def delete_by_announcement_id(announcement_id: int) -> int:
        """
        根据公告 ID 删除所有附件
        :param announcement_id: 公告ID
        :return: 成功删除的记录数量
        """
        sql = "DELETE FROM announcement_attachment WHERE announcement_id = %s"
        with get_cursor() as cursor:
            cursor.execute(sql, (announcement_id,))
            return cursor.rowcount
