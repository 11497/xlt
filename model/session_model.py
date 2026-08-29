from typing import Optional
from datetime import datetime

from pydantic import BaseModel, Field


SESSION_NAME_MIN_LENGTH = 1
SESSION_NAME_MAX_LENGTH = 30
DEFAULT_SESSION_NAME = "新建会话"


def normalize_session_name(name: str, fallback: str = DEFAULT_SESSION_NAME) -> str:
    """取首个非空行并将会话名称规范化为 1-30 个字符。"""
    def normalize_candidate(value: str) -> str:
        if not isinstance(value, str):
            return ""
        first_non_empty_line = next(
            (line.strip() for line in str(value).splitlines() if line.strip()),
            "",
        )
        return first_non_empty_line[:SESSION_NAME_MAX_LENGTH]

    normalized = normalize_candidate(name)
    if normalized:
        return normalized

    normalized_fallback = normalize_candidate(fallback)
    return normalized_fallback or DEFAULT_SESSION_NAME


def validate_session_name(name: str) -> str:
    """严格校验用户或其他已验证调用方提供的会话名称。"""
    if not isinstance(name, str) or not (
        SESSION_NAME_MIN_LENGTH <= len(name) <= SESSION_NAME_MAX_LENGTH
    ):
        raise ValueError(
            f"会话名称长度必须为 {SESSION_NAME_MIN_LENGTH}-"
            f"{SESSION_NAME_MAX_LENGTH} 个字符"
        )
    return name


class Session(BaseModel):
    """Session 数据模型，对应 xlt.session 表"""
    user_id: int = Field(ge=1)
    name: str = Field(
        min_length=SESSION_NAME_MIN_LENGTH,
        max_length=SESSION_NAME_MAX_LENGTH,
    )
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None
    id: Optional[int] = Field(default=None, ge=1)  # 新建时 id 为 None，查询时自动填充

    def to_dict(self) -> dict:
        return self.model_dump()

    @classmethod
    def from_row(cls, row: dict) -> "Session":
        """
        从数据库查询结果构建 Session 对象
        :param row: 数据库查询结果行
        :return: Session 对象
        """
        return cls.model_validate(row)
