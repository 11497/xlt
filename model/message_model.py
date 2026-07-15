from dataclasses import dataclass, field, asdict
from typing import Optional, Any
import json

from datetime import datetime


@dataclass
class Message:
    """Message 数据模型，对应 xlt.message 表"""
    session_id: int
    role: str
    content: dict[str, Any]
    create_time: datetime
    id: Optional[int] = field(default=None)  # 新建时 id 为 None，查询时自动填充

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_row(cls, row: dict) -> "Message":
        """
        从数据库查询结果构建 Message 对象
        :param row: 数据库查询结果行
        :return: Message 对象
        """
        # 如果数据库驱动未自动解析JSON，需手动loads；若已自动解析则直接使用 row["content"]
        content_data = row["content"]
        if isinstance(content_data, str):
            content_data = json.loads(content_data)

        return cls(
            id=row["id"],
            session_id=row["session_id"],
            role=row["role"],
            content=content_data,
            create_time=row["create_time"],
        )
