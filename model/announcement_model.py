from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field


class Announcement(BaseModel):
    """Announcement 数据模型，对应 xlt.announcement 表"""
    title: str = Field(min_length=1, max_length=255)
    content: str = Field(min_length=1)
    is_top: int = Field(default=0, ge=0, le=1)  # 默认不置顶
    create_time: datetime = Field(default_factory=datetime.now)
    update_time: datetime = Field(default_factory=datetime.now)
    id: Optional[int] = Field(default=None, ge=1)  # 新建时 id 为 None，查询时自动填充

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict) -> "Announcement":
        """
        从数据库查询结果构建 Announcement 对象
        :param row: 数据库查询结果行
        :return: Announcement 对象
        """
        return cls.model_validate(row)
