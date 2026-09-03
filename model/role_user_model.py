from typing import Optional

from datetime import datetime

from pydantic import BaseModel, Field


class RoleUser(BaseModel):
    """RoleUser 数据模型，对应 xlt.role_user 表"""
    role_id: int = Field(ge=1)
    user_id: int = Field(ge=1)

    is_deleted: int = Field(default=0, ge=0, le=1, init=False, exclude=True)
    deleted_at: Optional[datetime] = Field(default=None, init=False, exclude=True)

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
