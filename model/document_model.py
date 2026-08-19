from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class Document(BaseModel):
    """Document 数据模型，对应 xlt.document 表"""
    knowledge_base_id: int = Field(ge=1)
    filename: str = Field(min_length=1, max_length=255)
    storage_path: str = Field(min_length=1, max_length=500)
    create_time: datetime
    update_time: datetime
    id: Optional[int] = Field(default=None, ge=1)  # 新建时 id 为 None，查询时自动填充

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict) -> "Document":
        """
        从数据库查询结果构建 Document 对象
        :param row: 数据库查询结果行
        :return: Document 对象
        """
        return cls.model_validate(row)
