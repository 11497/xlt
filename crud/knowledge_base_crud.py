from typing import List, Optional

from db.db_connection import get_cursor
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
