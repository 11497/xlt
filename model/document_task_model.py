from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class DocumentTask(BaseModel):
    """DocumentTask 数据模型，对应 xlt.document_task 表"""
    model_config = ConfigDict(extra="forbid")
    task_type: str = Field(min_length=1, max_length=20)  # 任务类型：index（索引）/ delete（删除）
    document_id: int = Field(ge=0)
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
    claimed_by: Optional[str] = None
    claimed_at: Optional[datetime] = None

    @model_validator(mode="after")
    def validate_document_id(self) -> "DocumentTask":
        if self.task_type == "delete_kb" and self.document_id != 0:
            raise ValueError("delete_kb 任务的 document_id 必须为 0")
        if self.task_type != "delete_kb" and self.document_id == 0:
            raise ValueError("只有 delete_kb 任务可以使用 document_id=0")
        return self

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
