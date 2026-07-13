from typing import List, Optional
from db.db_connection import get_cursor
from model.document_model import Document


class DocumentCRUD:

    @staticmethod
    def create(document: Document) -> int:
        """
        新增文档
        :return: 新插入记录的 id
        """
        sql = "INSERT INTO document (knowledge_base_id, filename, storage_path) VALUES (%s, %s, %s)"
        with get_cursor() as cursor:
            cursor.execute(sql, (document.knowledge_base_id, document.filename, document.storage_path))
            return cursor.lastrowid

    @staticmethod
    def get_by_id(document_id: int) -> Optional[Document]:
        """根据 ID 查询单个文档"""
        sql = "SELECT * FROM document WHERE id = %s"
        with get_cursor() as cursor:
            cursor.execute(sql, (document_id,))
            row = cursor.fetchone()
            return Document.from_row(row) if row else None

    @staticmethod
    def get_by_knowledge_base_id(knowledge_base_id: int) -> List[Document]:
        """根据知识库 ID 查询所有文档"""
        sql = "SELECT * FROM document WHERE knowledge_base_id = %s ORDER BY create_time DESC"
        with get_cursor() as cursor:
            cursor.execute(sql, (knowledge_base_id,))
            rows = cursor.fetchall()
            return [Document.from_row(r) for r in rows]

    @staticmethod
    def get_all() -> List[Document]:
        """查询所有文档"""
        sql = "SELECT * FROM document ORDER BY create_time DESC"
        with get_cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [Document.from_row(r) for r in rows]

    @staticmethod
    def update(document_id: int, filename: str, storage_path: str) -> bool:
        """
        根据 ID 更新文档文件名和存储路径
        :return: 是否成功更新了记录
        """
        if document_id is None:
            raise ValueError("更新操作需要提供 document_id")
        sql = "UPDATE document SET filename = %s, storage_path = %s, update_time = NOW() WHERE id = %s"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, (filename, storage_path, document_id))
            return affected > 0

    @staticmethod
    def delete(document_id: int) -> bool:
        """
        根据 ID 删除文档
        :return: 是否成功删除了记录
        """
        sql = "DELETE FROM document WHERE id = %s"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, (document_id,))
            return affected > 0

    @staticmethod
    def batch_delete(document_ids: List[int]) -> int:
        """
        批量删除文档
        :param document_ids: 要删除的文档ID列表
        :return: 成功删除的记录数量
        """
        if not document_ids:
            return 0

        placeholders = ','.join(['%s'] * len(document_ids))
        sql = f"DELETE FROM document WHERE id IN ({placeholders})"
        with get_cursor() as cursor:
            cursor.execute(sql, document_ids)
            return cursor.rowcount

    @staticmethod
    def delete_by_knowledge_base_id(knowledge_base_id: int) -> int:
        """
        根据知识库 ID 删除所有文档
        :param knowledge_base_id: 知识库ID
        :return: 成功删除的记录数量
        """
        sql = "DELETE FROM document WHERE knowledge_base_id = %s"
        with get_cursor() as cursor:
            cursor.execute(sql, (knowledge_base_id,))
            return cursor.rowcount