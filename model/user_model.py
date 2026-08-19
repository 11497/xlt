from typing import Optional

from pydantic import BaseModel, Field


class User(BaseModel):
    """User 数据模型，对应 xlt.user 表"""
    username: str = Field(min_length=4, max_length=15)
    password: str = Field(min_length=6, max_length=20)
    is_admin: int = Field(default=0, ge=0, le=1)
    id: Optional[int] = None

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict) -> "User":
        """
        从数据库查询结果构建 User 对象
        :param row: 数据库查询结果行
        :return: User 对象
        """
        return cls.model_validate(row)