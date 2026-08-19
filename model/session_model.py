from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field


class Session(BaseModel):
    """Session 数据模型，对应 xlt.session 表"""
    user_id: int = Field(ge=1)
    name: str = Field(min_length=1, max_length=255)
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    id: Optional[int] = Field(default=None, ge=1)  # 新建时 id 为 None，查询时自动填充

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict) -> "Session":
        """
        从数据库查询结果构建 Session 对象
        :param row: 数据库查询结果行
        :return: Session 对象
        """
        return cls.model_validate(row)
