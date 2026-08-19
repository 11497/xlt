from pydantic import BaseModel, Field


class RoleUser(BaseModel):
    """RoleUser 数据模型，对应 xlt.role_user 表"""
    role_id: int = Field(ge=1)
    user_id: int = Field(ge=1)

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict) -> "RoleUser":
        """
        从数据库查询结果构建 RoleUser 对象
        :param row: 数据库查询结果行
        :return: RoleUser 对象
        """
        return cls.model_validate(row)
