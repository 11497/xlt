from typing import List, Optional
from util.db_util import get_cursor
from model.role_model import Role


class RoleCRUD:

    @staticmethod
    def create(role: Role) -> int:
        """
        新增角色
        :return: 新插入记录的 id
        """
        sql = "INSERT INTO role (name) VALUES (%s)"
        with get_cursor() as cursor:
            cursor.execute(sql, (role.name,))
            return cursor.lastrowid

    @staticmethod
    def get_by_name(name: str) -> Optional[Role]:
        """根据 name 查询单个角色"""
        sql = "SELECT * FROM role WHERE name = %s"
        with get_cursor() as cursor:
            cursor.execute(sql, (name,))
            row = cursor.fetchone()
            return Role.from_row(row) if row else None

    @staticmethod
    def get_by_id(role_id: int) -> Optional[Role]:
        """根据 ID 查询单个角色"""
        sql = "SELECT * FROM role WHERE id = %s"
        with get_cursor() as cursor:
            cursor.execute(sql, (role_id,))
            row = cursor.fetchone()
            return Role.from_row(row) if row else None

    @staticmethod
    def get_all() -> List[Role]:
        """查询所有角色"""
        sql = "SELECT * FROM role"
        with get_cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [Role.from_row(r) for r in rows]

    @staticmethod
    def update_name(role_id: int, name: str) -> bool:
        """
        根据 ID 更新角色名
        :return: 是否成功更新了记录
        """
        if role_id is None:
            raise ValueError("更新操作需要提供 role_id")
        sql = "UPDATE role SET name = %s WHERE id = %s"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, (name, role_id))
            return affected > 0

    @staticmethod
    def delete(role_id: int) -> bool:
        """
        根据 ID 删除角色
        :return: 是否成功删除了记录
        """
        sql = "DELETE FROM role WHERE id = %s"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, (role_id,))
            return affected > 0