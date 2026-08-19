from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field


class AnnouncementAttachment(BaseModel):
    """AnnouncementAttachment 数据模型，对应 xlt.announcement_attachment 表"""
    announcement_id: int = Field(ge=1)
    filename: str = Field(min_length=1, max_length=255)
    storage_path: str = Field(min_length=1, max_length=500)
    upload_time: datetime = Field(default_factory=datetime.now)
    id: Optional[int] = Field(default=None, ge=1)  # 新建时 id 为 None，查询时自动填充

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict) -> "AnnouncementAttachment":
        """
        从数据库查询结果构建 AnnouncementAttachment 对象
        :param row: 数据库查询结果行
        :return: AnnouncementAttachment 对象
        """
        return cls.model_validate(row)
