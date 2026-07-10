from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Announcement:
    """Announcement 数据模型，对应 xlt.announcement 表"""
    content: str
    created_time: datetime
    updated_time: datetime
    id: Optional[int] = field(default=None)  # 新建时 id 为 None，查询时自动填充

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_row(cls, row: dict) -> "Announcement":
        """从数据库查询结果构建 Announcement 对象"""
        return cls(
            id=row["id"],
            content=row["content"],
            created_time=row["created_time"],
            updated_time=row["updated_time"],
        )