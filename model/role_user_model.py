from dataclasses import dataclass, asdict


@dataclass
class RoleUser:
    """RoleUser 数据模型，对应 xlt.role_user 表"""
    role_id: int
    user_id: int

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_row(cls, row: dict) -> "RoleUser":
        """
        从数据库查询结果构建 RoleUser 对象
        :param row: 数据库查询结果行
        :return: RoleUser 对象
        """
        return cls(
            role_id=row["role_id"],
            user_id=row["user_id"],
        )