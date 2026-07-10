from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class Session:
    """Session 数据模型，对应 xlt.session 表"""
    user_id: int
    id: Optional[int] = field(default=None)  # 新建时 id 为 None，查询时自动填充

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_row(cls, row: dict) -> "Session":
        """从数据库查询结果构建 Session 对象"""
        return cls(
            id=row["id"],
            user_id=row["user_id"],
        )