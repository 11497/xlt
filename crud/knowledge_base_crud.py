from typing import List, Optional, Tuple

from util.db_util import get_cursor
from model.knowledge_base_model import KnowledgeBase


class KnowledgeBaseCRUD:

    @staticmethod
    def create(knowledge_base: KnowledgeBase) -> int:
        """
        创建知识库
        :param knowledge_base: KnowledgeBase对象
        :return: 新插入记录的 id
        """
        sql = "INSERT INTO knowledge_base (name) VALUES (%s)"
        with get_cursor() as cursor:
            cursor.execute(sql, (knowledge_base.name,))
            return cursor.lastrowid

    @staticmethod
    def get_by_id(knowledge_base_id: int) -> Optional[KnowledgeBase]:
        """
        根据 ID 查询单个知识库
        :param knowledge_base_id: 知识库ID
        :return: KnowledgeBase对象或None
        """
        sql = "SELECT * FROM knowledge_base WHERE id = %s"
        with get_cursor() as cursor:
            cursor.execute(sql, (knowledge_base_id,))
            row = cursor.fetchone()
            return KnowledgeBase.from_row(row) if row else None

    @staticmethod
    def update(knowledge_base: KnowledgeBase) -> bool:
        """
        修改知识库
        :param knowledge_base: KnowledgeBase对象
        :return: 操作是否成功
        """
        if knowledge_base.id is None:
            raise ValueError("更新操作需要提供 knowledge_base.id")
        sql = "UPDATE knowledge_base SET name = %s WHERE id = %s"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, (knowledge_base.name, knowledge_base.id))
            return affected > 0

    @staticmethod
    def get_all() -> List[KnowledgeBase]:
        """
        查看所有知识库
        :return: 所有知识库的列表
        """
        sql = "SELECT * FROM knowledge_base"
        with get_cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [KnowledgeBase.from_row(r) for r in rows]

    @staticmethod
    def get_page(page: int = 1, page_size: int = 10) -> Tuple[List[KnowledgeBase], int]:
        """
        分页查询知识库
        :param page: 页码（从1开始）
        :param page_size: 每页条数
        :return: (知识库列表, 总记录数)
        """
        offset = (page - 1) * page_size

        sql_count = "SELECT COUNT(*) AS total FROM knowledge_base"
        sql_data = "SELECT * FROM knowledge_base LIMIT %s OFFSET %s"

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
            knowledge_bases = [KnowledgeBase.from_row(r) for r in rows]

        return knowledge_bases, total

    @staticmethod
    def delete(knowledge_base_id: int) -> bool:
        """
        删除知识库
        :param knowledge_base_id: 知识库ID
        :return: 操作是否成功
        """
        sql = "DELETE FROM knowledge_base WHERE id = %s"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, (knowledge_base_id,))
            return affected > 0

    @staticmethod
    def search(content: str) -> List[KnowledgeBase]:
        """
        根据用户名或ID查询用户
        :param content: 搜索内容
        :return: 用户列表
        """
        knowledge_bases = []

        sql1 = "SELECT * FROM knowledge_base WHERE id = %s"
        with get_cursor() as cursor:
            cursor.execute(sql1, (content,))
            rows = cursor.fetchall()

            if rows:
                for row in rows:
                    knowledge_bases.append(KnowledgeBase.from_row(row))

        sql2 = "SELECT * FROM knowledge_base WHERE name LIKE %s"
        with get_cursor() as cursor:
            cursor.execute(sql2, (f"%{content}%",))
            rows = cursor.fetchall()

            if rows:
                for row in rows:
                    knowledge_bases.append(KnowledgeBase.from_row(row))

        return knowledge_bases