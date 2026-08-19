from typing import Optional

from pydantic import BaseModel, Field


class Role(BaseModel):
    """Role 数据模型，对应 xlt.role 表"""
    name: str = Field(min_length=1, max_length=255)
    id: Optional[int] = Field(default=None, ge=1)  # 新建时 id 为 None，查询时自动填充

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict) -> "Role":
        """
        从数据库查询结果构建 Role 对象
        :param row: 数据库查询结果行
        :return: Role 对象
        """
        return cls.model_validate(row)
