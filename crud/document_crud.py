from typing import List, Optional, Tuple

from util.db_util import get_cursor
from model.document_model import Document


class DocumentCRUD:

    @staticmethod
    def create(document: Document) -> int:
        """
        新增文档（初始状态为 pending）
        :param document: 文档对象
        :return: 新插入记录的 id
        """
        sql = ("INSERT INTO document (knowledge_base_id, filename, storage_path, status) "
               "VALUES (%s, %s, %s, %s)")
        with get_cursor() as cursor:
            cursor.execute(sql, (
                document.knowledge_base_id,
                document.filename,
                document.storage_path,
                document.status or "pending"
            ))
            return cursor.lastrowid

    @staticmethod
    def batch_create(documents: list) -> int:
        """
        批量新增文档
        :param documents: 文档列表，每个元素为 (knowledge_base_id, filename, storage_path) 元组
        :return: 成功插入的记录数
        """
        if not documents:
            return 0
        sql = "INSERT INTO document (knowledge_base_id, filename, storage_path) VALUES (%s, %s, %s)"
        with get_cursor() as cursor:
            affected = cursor.executemany(sql, documents)
            return affected

    @staticmethod
    def get_by_id(document_id: int) -> Optional[Document]:
        """
        根据 ID 查询单个文档
        :param document_id: 文档ID
        :return: 文档对象（如果存在）
        """
        sql = "SELECT * FROM document WHERE id = %s"
        with get_cursor() as cursor:
            cursor.execute(sql, (document_id,))
            row = cursor.fetchone()
            return Document.from_row(row) if row else None

    @staticmethod
    def get_by_knowledge_base_id(knowledge_base_id: int) -> List[Document]:
        """
        根据知识库 ID 查询所有文档
        :param knowledge_base_id: 知识库ID
        :return: 文档对象列表
        """
        sql = "SELECT * FROM document WHERE knowledge_base_id = %s ORDER BY create_time DESC"
        with get_cursor() as cursor:
            cursor.execute(sql, (knowledge_base_id,))
            rows = cursor.fetchall()
            return [Document.from_row(r) for r in rows]

    @staticmethod
    def get_all() -> List[Document]:
        """
        查询所有文档
        :return: 文档对象列表
        """
        sql = "SELECT * FROM document ORDER BY create_time DESC"
        with get_cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [Document.from_row(r) for r in rows]

    @staticmethod
    def get_by_status(status: str, limit: int = 100) -> List[Document]:
        """
        按状态查询文档
        :param status: 文档状态
        :param limit: 返回数量上限
        :return: 文档对象列表
        """
        sql = "SELECT * FROM document WHERE status = %s ORDER BY id ASC LIMIT %s"
        with get_cursor() as cursor:
            cursor.execute(sql, (status, limit))
            rows = cursor.fetchall()
            return [Document.from_row(r) for r in rows]

    @staticmethod
    def update(document_id: int, filename: str, storage_path: str) -> bool:
        """
        根据 ID 更新文档文件名和存储路径
        :param document_id: 文档ID
        :param filename: 新的文件名
        :param storage_path: 新的存储路径
        :return: 是否成功更新了记录
        """
        if document_id is None:
            raise ValueError("更新操作需要提供 document_id")
        sql = "UPDATE document SET filename = %s, storage_path = %s, update_time = NOW() WHERE id = %s"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, (filename, storage_path, document_id))
            return affected > 0

    @staticmethod
    def update_status(
            document_id: int,
            status: str,
            error_message: Optional[str] = None,
            retry_count: Optional[int] = None,
            chunk_count: Optional[int] = None
    ) -> bool:
        """
        更新文档状态
        :param document_id: 文档ID
        :param status: 目标状态
        :param error_message: 失败原因（可选）
        :param retry_count: 重试次数（可选）
        :param chunk_count: 切片数（可选）
        :return: 是否更新成功
        """
        sets = ["status = %s", "update_time = NOW()"]
        params: list = [status]
        if error_message is not None:
            sets.append("error_message = %s")
            params.append(error_message)
        if retry_count is not None:
            sets.append("retry_count = %s")
            params.append(retry_count)
        if chunk_count is not None:
            sets.append("chunk_count = %s")
            params.append(chunk_count)
        params.append(document_id)
        sql = f"UPDATE document SET {', '.join(sets)} WHERE id = %s"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, tuple(params))
            return affected > 0

    @staticmethod
    def delete(document_id: int) -> bool:
        """
        根据 ID 删除文档
        :param document_id: 文档ID
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

    @staticmethod
    def get_page_by_knowledge_base(
            knowledge_base_id: int,
            page: int = 1,
            page_size: int = 10
    ) -> Tuple[List[Document], int]:
        """
        按知识库分页查询文档
        :param knowledge_base_id: 知识库ID
        :param page: 页码（从1开始）
        :param page_size: 每页条数
        :return: (文档列表, 总记录数)
        """
        offset = (page - 1) * page_size

        sql_count = "SELECT COUNT(*) AS total FROM document WHERE knowledge_base_id = %s"
        sql_data = ("SELECT * FROM document WHERE knowledge_base_id = %s "
                    "ORDER BY create_time DESC LIMIT %s OFFSET %s")

        with get_cursor() as cursor:
            # 获取总数（兼容字典游标和元组游标）
            cursor.execute(sql_count, (knowledge_base_id,))
            count_row = cursor.fetchone()
            if isinstance(count_row, dict):
                total = count_row.get("total", count_row.get("COUNT(*)", 0))
            else:
                total = count_row[0] if count_row else 0

            # 获取分页数据
            cursor.execute(sql_data, (knowledge_base_id, page_size, offset))
            rows = cursor.fetchall()
            documents = [Document.from_row(r) for r in rows]

        return documents, total
