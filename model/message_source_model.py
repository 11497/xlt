from datetime import datetime
from typing import Optional

from pydantic import Field

from model.schema_utils import (
    SoftDeleteModel,
    exclude_internal_soft_delete_fields,
)


class MessageSource(SoftDeleteModel):
    """回答来源引用数据模型，随消息业务软删除。"""

    model_config = {
        "extra": "forbid",
        "json_schema_extra": exclude_internal_soft_delete_fields,
    }

    id: Optional[int] = Field(default=None, ge=1)
    message_id: Optional[int] = Field(default=None, ge=1)
    session_id: Optional[int] = Field(default=None, ge=1)
    source_content_id: Optional[int] = Field(default=None, ge=1)
    knowledge_base_id: int = Field(ge=1)
    document_id: int = Field(ge=1)
    chunk_id: str = Field(min_length=1, max_length=64)
    chunk_index: int = Field(ge=0)
    filename: str = Field(min_length=1, max_length=255)
    rerank_score: Optional[float] = None
    recall_source: Optional[str] = None
    sort_order: int = Field(default=0, ge=0)
    create_time: Optional[datetime] = None

    # 写入前由编排层携带的正文快照，不随模型序列化返回。
    content: str = Field(default="", exclude=True, repr=False)

    is_deleted: int = Field(default=0, ge=0, le=1, init=False, exclude=True)
    deleted_at: Optional[datetime] = Field(default=None, init=False, exclude=True)

    @classmethod
    def from_row(cls, row: dict) -> "MessageSource":
        return cls.model_construct(
            id=row["id"],
            message_id=row["message_id"],
            session_id=row["session_id"],
            source_content_id=row["source_content_id"],
            knowledge_base_id=row["knowledge_base_id"],
            document_id=row["document_id"],
            chunk_id=row["chunk_id"],
            chunk_index=row["chunk_index"],
            filename=row["filename"],
            rerank_score=row.get("rerank_score"),
            recall_source=row.get("recall_source"),
            sort_order=row.get("sort_order", 0),
            create_time=row.get("create_time"),
            is_deleted=row.get("is_deleted", 0),
            deleted_at=row.get("deleted_at"),
        )
