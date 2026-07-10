from dataclasses import dataclass, field, asdict
from typing import Optional

from datetime import datetime


@dataclass
class Message:
    """Message 数据模型，对应 xlt.message 表"""
    session_id: int
    content: str
    created_time: datetime
    id: Optional[int] = field(default=None)  # 新建时 id 为 None，查询时自动填充

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_row(cls, row: dict) -> "Message":
        """从数据库查询结果构建 Message 对象"""
        return cls(
            id=row["id"],
            session_id=row["session_id"],
            content=row["content"],
            created_time=row["created_time"],
        )
