from model.schema_utils import SoftDeleteModel, exclude_internal_soft_delete_fields

from datetime import datetime
from typing import Literal, Optional

from pydantic import ConfigDict, Field


class Message(SoftDeleteModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra=exclude_internal_soft_delete_fields,
    )
    """Message 数据模型，对应 xlt.message 表"""
    session_id: int = Field(ge=1)
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)
    create_time: datetime
    id: Optional[int] = Field(default=None, ge=1)  # 新建时 id 为 None，查询时自动填充
    rewritten_content: Optional[str] = None
    # 恶意/敏感判定针对用户输入；拒绝回复本身仍标记为 0。
    is_malicious: int = Field(default=0, ge=0, le=1)
    # 仅 assistant 因用户手动停止保存非空片段时为 1。
    is_stopped: int = Field(default=0, ge=0, le=1)



    is_deleted: int = Field(default=0, ge=0, le=1, init=False, exclude=True)
    deleted_at: Optional[datetime] = Field(default=None, init=False, exclude=True)

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict) -> "Message":
        """
        从数据库查询结果构建 Message 对象
        :param row: 数据库查询结果行
        :return: Message 对象
        """
        return cls.model_construct(**row)
