from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class DocumentTask(BaseModel):
    """DocumentTask 数据模型，对应 xlt.document_task 表"""
    task_type: str = Field(min_length=1, max_length=20)  # index / delete
    document_id: int = Field(ge=1)
    knowledge_base_id: int = Field(ge=1)
    status: str = Field(default="pending", max_length=20)
    payload: Optional[str] = None
    error_message: Optional[str] = None
    retry_count: int = Field(default=0, ge=0)
    max_retries: int = Field(default=5, ge=1)
    next_retry_at: Optional[datetime] = None
    result_json: Optional[str] = None
    id: Optional[int] = Field(default=None, ge=1)
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict) -> "DocumentTask":
        """
        从数据库查询结果构建 DocumentTask 对象
        :param row: 数据库查询结果行
        :return: DocumentTask 对象
        """
        return cls.model_validate(row)
