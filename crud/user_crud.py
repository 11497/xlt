from typing import List, Optional
from db.db_connection import get_cursor
from model.user_model import User


class UserCRUD:

    @staticmethod
    def create(user: User) -> int:
        """
        新增用户
        :return: 新插入记录的 id
        """
        sql = "INSERT INTO user (username, password) VALUES (%s, %s)"
        with get_cursor() as cursor:
            cursor.execute(sql, (user.username, user.password))
            return cursor.lastrowid

    @staticmethod
    def get_by_username(username: str) -> Optional[User]:
        """根据 username 查询单个用户"""
        sql = "SELECT * FROM user WHERE username = %s"
        with get_cursor() as cursor:
            cursor.execute(sql, (username,))
            row = cursor.fetchone()
            return User.from_row(row) if row else None

    @staticmethod
    def get_by_id(user_id: int) -> Optional[User]:
        """根据 ID 查询单个用户"""
        sql = "SELECT * FROM user WHERE id = %s"
        with get_cursor() as cursor:
            cursor.execute(sql, (user_id,))
            row = cursor.fetchone()
            return User.from_row(row) if row else None

    @staticmethod
    def get_all() -> List[User]:
        """查询所有用户"""
        sql = "SELECT * FROM user"
        with get_cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [User.from_row(r) for r in rows]

    @staticmethod
    def update(user: User) -> bool:
        """
        根据 ID 更新用户信息（全量更新）
        :return: 是否成功更新了记录
        """
        if user.id is None:
            raise ValueError("更新操作需要提供 user.id")
        sql = "UPDATE user SET username = %s, password = %s WHERE id = %s"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, (user.username, user.password, user.id))
            return affected > 0

    @staticmethod
    def delete(user_id: int) -> bool:
        """
        根据 ID 删除用户
        :return: 是否成功删除了记录
        """
        sql = "DELETE FROM user WHERE id = %s"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, (user_id,))
            return affected > 0