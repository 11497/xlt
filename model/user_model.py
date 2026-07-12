from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class User:
    """User 数据模型，对应 xlt.user 表"""
    username: str
    password: str
    is_admin: int
    id: Optional[int] = field(default=None)  # 新建时 id 为 None，查询时自动填充

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_row(cls, row: dict) -> "User":
        """从数据库查询结果构建 User 对象"""
        return cls(
            id=row["id"],
            username=row["username"],
            password=row["password"],
            is_admin=row["is_admin"],
        )