from dataclasses import dataclass, field, asdict
from typing import Optional
from datetime import datetime


@dataclass
class Session:
    """Session 数据模型，对应 xlt.session 表"""
    user_id: int
    name: str
    create_time: Optional[datetime] = field(default=None)
    update_time: Optional[datetime] = field(default=None)
    id: Optional[int] = field(default=None)  # 新建时 id 为 None，查询时自动填充

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_row(cls, row: dict) -> "Session":
        """
        从数据库查询结果构建 Session 对象
        :param row: 数据库查询结果行
        :return: Session 对象
        """
        return cls(
            id=row["id"],
            user_id=row["user_id"],
            name=row["name"],
            create_time=row.get("create_time"),
            update_time=row.get("update_time"),
        )