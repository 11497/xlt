from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime


@dataclass
class AnnouncementAttachment:
    """AnnouncementAttachment 数据模型，对应 xlt.announcement_attachment 表"""
    announcement_id: int
    filename: str
    storage_path: str
    upload_time: datetime = field(default_factory=datetime.now)
    id: Optional[int] = field(default=None)  # 新建时 id 为 None，查询时自动填充

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_row(cls, row: dict) -> "AnnouncementAttachment":
        """
        从数据库查询结果构建 AnnouncementAttachment 对象
        :param row: 数据库查询结果行
        :return: AnnouncementAttachment 对象
        """
        return cls(
            id=row["id"],
            announcement_id=row["announcement_id"],
            filename=row["filename"],
            storage_path=row["storage_path"],
            upload_time=row["upload_time"],
        )
