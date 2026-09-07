from model.schema_utils import SoftDeleteModel, exclude_internal_soft_delete_fields

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class UserRegistration(BaseModel):
    """普通用户注册请求，不允许设置管理员权限。"""
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra=exclude_internal_soft_delete_fields,
    )

    username: str = Field(min_length=4, max_length=15)
    password: str = Field(min_length=6, max_length=20, exclude=True, repr=False)


class User(SoftDeleteModel):
    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra=exclude_internal_soft_delete_fields,
    )
    """User 数据模型，对应 xlt.user 表"""
    username: str = Field(min_length=4, max_length=15)
    password: str = Field(min_length=6, max_length=20, exclude=True, repr=False)
    is_admin: int = Field(default=0, ge=0, le=1)
    id: Optional[int] = None

    is_deleted: int = Field(default=0, ge=0, le=1, init=False, exclude=True)
    deleted_at: Optional[datetime] = Field(default=None, init=False, exclude=True)

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict) -> "User":
        """
        从数据库查询结果构建 User 对象
        :param row: 数据库查询结果行
        :return: User 对象
        """
        # 数据库保存的是长度超过明文约束的 Argon2id 哈希，数据库行已由表结构保证类型。
        return cls.model_construct(**row)
