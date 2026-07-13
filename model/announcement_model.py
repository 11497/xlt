from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime


@dataclass
class Announcement:
    """Announcement 数据模型，对应 xlt.announcement 表"""
    title: str
    content: str
    is_top: int = 0  # 默认不置顶
    create_time: datetime = field(default_factory=datetime.now)
    update_time: datetime = field(default_factory=datetime.now)
    id: Optional[int] = field(default=None)  # 新建时 id 为 None，查询时自动填充

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_row(cls, row: dict) -> "Announcement":
        """从数据库查询结果构建 Announcement 对象"""
        return cls(
            id=row["id"],
            title=row["title"],
            content=row["content"],
            is_top=row["is_top"],
            create_time=row["create_time"],
            update_time=row["update_time"],
        )
