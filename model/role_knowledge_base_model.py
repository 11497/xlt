from pydantic import BaseModel, Field


class RoleKnowledgeBase(BaseModel):
    """RoleKnowledgeBase 数据模型，对应 xlt.role_knowledge_base 表"""
    role_id: int = Field(ge=1)
    knowledge_base_id: int = Field(ge=1)

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict) -> "RoleKnowledgeBase":
        """
        从数据库查询结果构建 RoleKnowledgeBase 对象
        :param row: 数据库查询结果行
        :return: RoleKnowledgeBase 对象
        """
        return cls.model_validate(row)
