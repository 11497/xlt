from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, Field


class Message(BaseModel):
    """Message 数据模型，对应 xlt.message 表"""
    session_id: int = Field(ge=1)
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1)
    create_time: datetime
    id: Optional[int] = Field(default=None, ge=1)  # 新建时 id 为 None，查询时自动填充
    rewritten_content: Optional[str] = None

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict) -> "Message":
        """
        从数据库查询结果构建 Message 对象
        :param row: 数据库查询结果行
        :return: Message 对象
        """
        return cls.model_validate(row)
