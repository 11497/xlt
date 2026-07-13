from typing import List, Optional
from db.db_connection import get_cursor
from model.announcement_model import Announcement


class AnnouncementCRUD:

    @staticmethod
    def create(announcement: Announcement) -> int:
        """
        新增公告
        :return: 新插入记录的 id
        """
        sql = "INSERT INTO announcement (title, content, is_top) VALUES (%s, %s, %s)"
        with get_cursor() as cursor:
            cursor.execute(sql, (announcement.title, announcement.content, announcement.is_top))
            return cursor.lastrowid

    @staticmethod
    def update_update_time(announcement_id: int) -> bool:
        """
        更新公告的 update_time 字段为当前时间
        :return: 是否成功更新了记录
        """
        if announcement_id is None:
            raise ValueError("更新操作需要提供 announcement_id")
        sql = "UPDATE announcement SET update_time = CURRENT_TIMESTAMP WHERE id = %s"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, (announcement_id,))
            return affected > 0

    @staticmethod
    def update(announcement_id: int, title: str, content: str, is_top: int) -> bool:
        """
        修改公告信息（title、content、is_top），同时更新 update_time
        :return: 是否成功更新了记录
        """
        if announcement_id is None:
            raise ValueError("更新操作需要提供 announcement_id")

        # 首先调用更新时间的方法
        AnnouncementCRUD.update_update_time(announcement_id)

        sql = "UPDATE announcement SET title = %s, content = %s, is_top = %s WHERE id = %s"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, (title, content, is_top, announcement_id))
            return affected > 0

    @staticmethod
    def batch_delete(announcement_ids: List[int]) -> int:
        """
        批量删除公告
        :param announcement_ids: 要删除的公告ID列表
        :return: 成功删除的记录数量
        """
        if not announcement_ids:
            return 0

        placeholders = ','.join(['%s'] * len(announcement_ids))
        sql = f"DELETE FROM announcement WHERE id IN ({placeholders})"
        with get_cursor() as cursor:
            cursor.execute(sql, announcement_ids)
            return cursor.rowcount

    @staticmethod
    def get_by_id(announcement_id: int) -> Optional[Announcement]:
        """根据 ID 查询单个公告"""
        sql = "SELECT * FROM announcement WHERE id = %s"
        with get_cursor() as cursor:
            cursor.execute(sql, (announcement_id,))
            row = cursor.fetchone()
            return Announcement.from_row(row) if row else None

    @staticmethod
    def get_all() -> List[Announcement]:
        """查询所有公告"""
        sql = "SELECT * FROM announcement ORDER BY is_top DESC, create_time DESC"
        with get_cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [Announcement.from_row(r) for r in rows]
