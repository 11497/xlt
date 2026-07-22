from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Message:
    """Message 数据模型，对应 xlt.message 表"""
    session_id: int
    role: str
    content: str
    create_time: datetime
    id: Optional[int] = field(default=None)  # 新建时 id 为 None，查询时自动填充
    rewritten_content: str = field(default="")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_row(cls, row: dict) -> "Message":
        """
        从数据库查询结果构建 Message 对象
        :param row: 数据库查询结果行
        :return: Message 对象
        """
        return cls(
            id=row["id"],
            session_id=row["session_id"],
            role=row["role"],
            content=row["content"],
            rewritten_content=row["rewritten_content"],
            create_time=row["create_time"],
        )
