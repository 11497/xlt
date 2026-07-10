from dataclasses import dataclass, field, asdict
from typing import Optional


@dataclass
class KnowledgeBase:
    """KnowledgeBase 数据模型，对应 xlt.knowledge_base 表"""
    name: str
    id: Optional[int] = field(default=None)  # 新建时 id 为 None，查询时自动填充

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_row(cls, row: dict) -> "KnowledgeBase":
        """从数据库查询结果构建 KnowledgeBase 对象"""
        return cls(
            id=row["id"],
            name=row["name"],
        )