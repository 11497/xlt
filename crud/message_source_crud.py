import hashlib
from typing import List, Optional

import pymysql

from crud.document_crud import get_filenames_by_document_ids
from model.message_model import Message
from model.message_source_model import MessageSource
from util.db_util import get_connection, get_cursor


def sha256_hex(content: str) -> str:
    """计算 UTF-8 字节流的 SHA-256 十六进制哈希。"""

    return hashlib.sha256(content.encode("utf-8")).hexdigest()


class SourceContentCRUD:
    """来源正文数据访问层，正文按内容哈希去重且不做更新。"""

    @staticmethod
    def get_id_by_content_hash(cursor, content_hash: str) -> Optional[int]:
        cursor.execute(
            "SELECT id FROM source_content WHERE content_hash = %s",
            (content_hash,)
        )
        row = cursor.fetchone()
        return row["id"] if row and isinstance(row, dict) else None

    @staticmethod
    def insert(cursor, content: str) -> int:
        """在当前事务中插入来源正文；并发唯一键冲突由 get_or_create 处理。"""
        content_hash = sha256_hex(content)
        cursor.execute(
            "INSERT INTO source_content (content_hash, content) VALUES (%s, %s)",
            (content_hash, content)
        )
        return cursor.lastrowid

    @staticmethod
    def get_or_create(cursor, content: str) -> int:
        """
        查询或创建正文 ID。
        并发插入相同内容时，若唯一键冲突则回查既有记录。
        :param cursor: 已开启事务的游标
        :param content: 送入模型的切片原文
        :return: 来源正文 ID
        """
        existing_id = SourceContentCRUD.get_id_by_content_hash(
            cursor,
            sha256_hex(content)
        )
        if existing_id is not None:
            return existing_id

        try:
            return SourceContentCRUD.insert(cursor, content)
        except pymysql.err.IntegrityError:
            # 并发事务可能已提交相同 hash，回查当前事务可见记录。
            existing_id = SourceContentCRUD.get_id_by_content_hash(
                cursor,
                sha256_hex(content)
            )
            if existing_id is not None:
                return existing_id
            raise


class MessageSourceCRUD:
    """回答来源引用数据访问层，引用随消息业务软删除。"""

    @staticmethod
    def batch_insert(cursor, sources: list[MessageSource]) -> int:
        if not sources:
            return 0

        cursor.executemany(
            """
            INSERT INTO message_source (
                message_id, session_id, source_content_id,
                knowledge_base_id, document_id, chunk_id, chunk_index,
                filename, rerank_score, recall_source, sort_order
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            [
                (
                    source.message_id,
                    source.session_id,
                    source.source_content_id,
                    source.knowledge_base_id,
                    source.document_id,
                    source.chunk_id,
                    source.chunk_index,
                    source.filename,
                    source.rerank_score,
                    source.recall_source,
                    source.sort_order,
                )
                for source in sources
            ]
        )
        return len(sources)

    @staticmethod
    def get_by_message_ids(message_ids: list[int]) -> list[dict]:
        """批量查询未删除来源引用及其正文快照。"""
        if not message_ids:
            return []

        placeholders = ",".join(["%s"] * len(message_ids))
        sql = f"""
            SELECT
                ms.id,
                ms.message_id,
                ms.session_id,
                ms.source_content_id,
                ms.knowledge_base_id,
                ms.document_id,
                ms.chunk_id,
                ms.chunk_index,
                ms.filename,
                ms.rerank_score,
                ms.recall_source,
                ms.sort_order,
                ms.create_time,
                sc.content
            FROM message_source ms
            JOIN source_content sc ON sc.id = ms.source_content_id
            WHERE ms.is_deleted = 0
              AND ms.message_id IN ({placeholders})
            ORDER BY ms.message_id ASC, ms.sort_order ASC, ms.id ASC
        """
        with get_cursor() as cursor:
            cursor.execute(sql, message_ids)
            rows = cursor.fetchall()
            return [_to_public_source(row) for row in rows]

    @staticmethod
    def soft_delete_by_session_id(cursor, session_id: int) -> int:
        cursor.execute(
            "UPDATE message_source SET is_deleted = 1, deleted_at = NOW() "
            "WHERE session_id = %s AND is_deleted = 0",
            (session_id,)
        )
        return cursor.rowcount

    @staticmethod
    def soft_delete_by_session_and_after(cursor, session_id: int, message_id: int) -> int:
        cursor.execute(
            "UPDATE message_source SET is_deleted = 1, deleted_at = NOW() "
            "WHERE session_id = %s AND message_id >= %s AND is_deleted = 0",
            (session_id, message_id)
        )
        return cursor.rowcount


def create_assistant_message_with_sources(
        message: Message,
        sources: list[MessageSource]
) -> int:
    """
    在同一事务中创建 assistant 消息、来源正文和来源引用。
    任一写入失败都会整体回滚，避免回答已提交但来源缺失。
    :param message: assistant 消息对象
    :param sources: 模型判定使用的切片快照列表
    :return: 新消息 ID
    """
    if message.role != "assistant":
        raise ValueError("只有 assistant 消息可以携带来源")

    with get_connection() as conn:
        cursor = conn.cursor(pymysql.cursors.DictCursor)
        try:
            cursor.execute(
                "INSERT INTO message (session_id, role, content, rewritten_content) "
                "VALUES (%s, %s, %s, %s)",
                (message.session_id, message.role, message.content, message.rewritten_content)
            )
            message_id = cursor.lastrowid

            for sort_order, source in enumerate(sources):
                source.message_id = message_id
                source.session_id = message.session_id
                source.sort_order = sort_order
                source.source_content_id = SourceContentCRUD.get_or_create(
                    cursor,
                    source.content
                )

            MessageSourceCRUD.batch_insert(cursor, sources)
            return message_id
        finally:
            cursor.close()


def get_sources_by_message_ids(message_ids: list[int]) -> list[dict]:
    """按消息 ID 批量查询未删除来源引用及其正文快照。"""
    return MessageSourceCRUD.get_by_message_ids(message_ids)


def get_sources_grouped_by_message_ids(message_ids: list[int]) -> dict[int, list[dict]]:
    """按消息 ID 批量查询来源并按 message_id 分组，避免 N+1 查询。"""
    grouped: dict[int, list[dict]] = {}
    if not message_ids:
        return grouped

    placeholders = ",".join(["%s"] * len(message_ids))
    sql = f"""
        SELECT
            ms.message_id,
            ms.chunk_id,
            ms.chunk_index,
            ms.document_id,
            ms.filename,
            ms.knowledge_base_id,
            ms.rerank_score,
            ms.recall_source,
            ms.sort_order,
            sc.content
        FROM message_source ms
        JOIN source_content sc ON sc.id = ms.source_content_id
        WHERE ms.is_deleted = 0
          AND ms.message_id IN ({placeholders})
        ORDER BY ms.message_id ASC, ms.sort_order ASC, ms.id ASC
    """
    with get_cursor() as cursor:
        cursor.execute(sql, message_ids)
        for row in cursor.fetchall():
            grouped.setdefault(row["message_id"], []).append(_to_public_source(row))
    return grouped


def _to_public_source(row: dict) -> dict:
    return {
        "chunk_id": row["chunk_id"],
        "chunk_index": row["chunk_index"],
        "document_id": row["document_id"],
        "filename": row["filename"],
        "knowledge_base_id": row["knowledge_base_id"],
        "content": row["content"],
        "rerank_score": row.get("rerank_score"),
        "recall_source": row.get("recall_source"),
        "sort_order": row.get("sort_order", 0),
    }


# 文档删除后无法回查文件名时使用统一占位，避免来源行出现空文件名。
UNKNOWN_DOCUMENT_NAME = "未知文档"


def build_message_sources(
        session_id: int,
        selected_chunks: List[dict]
) -> List[MessageSource]:
    """
    将模型选出的结构化切片转换为来源引用快照。
    :param session_id: assistant 消息所属会话 ID
    :param selected_chunks: 相关性判定选中的候选切片
    :return: 可随 assistant 消息写入的来源列表
    """
    if not selected_chunks:
        return []

    document_ids = sorted({
        document_id
        for document_id in (
            _parse_positive_int(chunk.get("metadata", {}).get("document_id"))
            for chunk in selected_chunks
        )
        if document_id is not None
    })
    filenames = get_filenames_by_document_ids(document_ids)

    sources: List[MessageSource] = []
    for chunk in selected_chunks:
        metadata = chunk.get("metadata", {})
        document_id = _parse_positive_int(metadata.get("document_id"))
        knowledge_base_id = _parse_positive_int(metadata.get("knowledge_base_id"))
        chunk_index = _parse_non_negative_int(metadata.get("chunk_index"))
        chunk_id = str(chunk.get("id", "")).strip()
        if document_id is None or knowledge_base_id is None or chunk_index is None:
            continue
        if not chunk_id or len(chunk_id) > 64:
            continue

        source = MessageSource(
            message_id=None,
            session_id=session_id,
            source_content_id=None,
            knowledge_base_id=knowledge_base_id,
            document_id=document_id,
            chunk_id=chunk_id,
            chunk_index=chunk_index,
            filename=filenames.get(document_id, UNKNOWN_DOCUMENT_NAME),
            rerank_score=_optional_float(chunk.get("rerank_score")),
            recall_source=chunk.get("source"),
            sort_order=0,
        )
        source.content = chunk.get("content", "")
        sources.append(source)

    return sources


def _parse_positive_int(value) -> Optional[int]:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed > 0 else None


def _parse_non_negative_int(value) -> Optional[int]:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return None
    return parsed if parsed >= 0 else None


def _optional_float(value) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None
