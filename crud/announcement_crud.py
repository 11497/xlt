from typing import List, Optional, Tuple
from util.db_util import get_cursor
from model.announcement_model import Announcement


class AnnouncementCRUD:

    @staticmethod
    def create(announcement: Announcement) -> int:
        """
        新增公告
        :param announcement: 公告对象
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
        :param announcement_id: 公告ID
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
        :param announcement_id: 公告ID
        :param title: 新的标题
        :param content: 新的内容
        :param is_top: 新的置顶状态（0/1）
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
        """
        根据 ID 查询单个公告
        :param announcement_id: 公告ID
        :return: 公告对象（如果存在）
        """
        sql = "SELECT * FROM announcement WHERE id = %s"
        with get_cursor() as cursor:
            cursor.execute(sql, (announcement_id,))
            row = cursor.fetchone()
            return Announcement.from_row(row) if row else None

    @staticmethod
    def get_all() -> List[Announcement]:
        """
        查询所有公告
        :return: 公告对象列表
        """
        sql = "SELECT * FROM announcement ORDER BY is_top DESC, create_time DESC"
        with get_cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [Announcement.from_row(r) for r in rows]

    @staticmethod
    def get_page(page: int = 1, page_size: int = 10) -> Tuple[List[Announcement], int]:
        """
        分页查询公告
        :param page: 页码（从1开始）
        :param page_size: 每页条数
        :return: (公告列表, 总记录数)
        """
        offset = (page - 1) * page_size

        sql_count = "SELECT COUNT(*) AS total FROM announcement"
        sql_data = "SELECT * FROM announcement ORDER BY is_top DESC, create_time DESC LIMIT %s OFFSET %s"

        with get_cursor() as cursor:
            # 获取总数（兼容字典游标和元组游标）
            cursor.execute(sql_count)
            count_row = cursor.fetchone()
            if isinstance(count_row, dict):
                total = count_row.get("total", count_row.get("COUNT(*)", 0))
            else:
                total = count_row[0] if count_row else 0

            # 获取分页数据
            cursor.execute(sql_data, (page_size, offset))
            rows = cursor.fetchall()
            announcements = [Announcement.from_row(r) for r in rows]

        return announcements, total

    @staticmethod
    def get_recent(limit: int = 5) -> Tuple[List[Announcement], int]:
        """查询最近发布的公告及公告总数。"""
        sql_count = "SELECT COUNT(*) AS total FROM announcement"
        sql_data = "SELECT * FROM announcement ORDER BY create_time DESC LIMIT %s"

        with get_cursor() as cursor:
            cursor.execute(sql_count)
            count_row = cursor.fetchone()
            if isinstance(count_row, dict):
                total = count_row.get("total", count_row.get("COUNT(*)", 0))
            else:
                total = count_row[0] if count_row else 0

            cursor.execute(sql_data, (limit,))
            announcements = [Announcement.from_row(row) for row in cursor.fetchall()]

        return announcements, total
