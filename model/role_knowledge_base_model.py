from dataclasses import dataclass, asdict


@dataclass
class RoleKnowledgeBase:
    """RoleKnowledgeBase 数据模型，对应 xlt.role_knowledge_base 表"""
    role_id: int
    knowledge_base_id: int

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_row(cls, row: dict) -> "RoleKnowledgeBase":
        """从数据库查询结果构建 RoleKnowledgeBase 对象"""
        return cls(
            role_id=row["role_id"],
            knowledge_base_id=row["knowledge_base_id"],
        )