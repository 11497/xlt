from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional


@dataclass
class Document:
    """Document 数据模型，对应 xlt.document 表"""
    knowledge_base_id: int
    name: str
    content: str
    created_time: datetime
    updated_time: datetime
    id: Optional[int] = field(default=None)  # 新建时 id 为 None，查询时自动填充

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_row(cls, row: dict) -> "Document":
        """从数据库查询结果构建 Document 对象"""
        return cls(
            id=row["id"],
            knowledge_base_id=row["knowledge_base_id"],
            name=row["name"],
            content=row["content"],
            created_time=row["created_time"],
            updated_time=row["updated_time"],
        )