from typing import Any

from pydantic import BaseModel, ConfigDict, model_validator


INTERNAL_SOFT_DELETE_FIELDS = frozenset(("is_deleted", "deleted_at"))


class SoftDeleteModel(BaseModel):
    """数据库行可带软删除字段，但客户端不能写入这些字段。"""

    model_config = ConfigDict(extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def reject_internal_fields(cls, value: Any) -> Any:
        if isinstance(value, dict):
            supplied = INTERNAL_SOFT_DELETE_FIELDS.intersection(value)
            if supplied:
                fields = ", ".join(sorted(supplied))
                raise ValueError(f"不允许设置内部字段：{fields}")
        return value


def exclude_internal_soft_delete_fields(schema: dict) -> None:
    """OpenAPI Schema 不展示内部逻辑删除字段。"""
    properties = schema.get("properties", {})
    properties.pop("is_deleted", None)
    properties.pop("deleted_at", None)
    required = schema.get("required", [])
    if isinstance(required, list):
        schema["required"] = [
            name for name in required if name not in ("is_deleted", "deleted_at")
        ]
