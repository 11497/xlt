from model.schema_utils import SoftDeleteModel, exclude_internal_soft_delete_fields

from typing import Optional

from datetime import datetime

from pydantic import ConfigDict, Field


class KnowledgeBase(SoftDeleteModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra=exclude_internal_soft_delete_fields,
    )
    """KnowledgeBase 数据模型，对应 xlt.knowledge_base 表"""
    name: str = Field(min_length=1, max_length=15)
    id: Optional[int] = Field(default=None, ge=1)  # 新建时 id 为 None，查询时自动填充

    is_deleted: int = Field(default=0, ge=0, le=1, init=False, exclude=True)
    deleted_at: Optional[datetime] = Field(default=None, init=False, exclude=True)

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict) -> "KnowledgeBase":
        """
        从数据库查询结果构建 KnowledgeBase 对象
        :param row: 数据库查询结果行
        :return: KnowledgeBase 对象
        """
        return cls.model_construct(**row)
