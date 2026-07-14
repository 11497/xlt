from typing import List, Optional
from util.db_util import get_cursor
from model.user_model import User


class UserCRUD:

    @staticmethod
    def create(user: User) -> int:
        """
        新增用户
        :param user: 用户对象
        :return: 新插入记录的 id
        """
        sql = "INSERT INTO user (username, password) VALUES (%s, %s)"
        with get_cursor() as cursor:
            cursor.execute(sql, (user.username, user.password))
            return cursor.lastrowid

    @staticmethod
    def get_by_username(username: str) -> Optional[User]:
        """
        根据用户名查询单个用户
        :param username: 用户名
        :return: 用户对象（如果存在）
        """
        sql = "SELECT * FROM user WHERE username = %s"
        with get_cursor() as cursor:
            cursor.execute(sql, (username,))
            row = cursor.fetchone()
            return User.from_row(row) if row else None

    @staticmethod
    def get_by_id(user_id: int) -> Optional[User]:
        """
        根据 ID 查询单个用户
        :param user_id: 用户ID
        :return: 用户对象（如果存在）
        """
        sql = "SELECT * FROM user WHERE id = %s"
        with get_cursor() as cursor:
            cursor.execute(sql, (user_id,))
            row = cursor.fetchone()
            return User.from_row(row) if row else None

    @staticmethod
    def get_all() -> List[User]:
        """
        查询所有用户
        :return: 用户对象列表
        """
        sql = "SELECT * FROM user"
        with get_cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [User.from_row(r) for r in rows]

    @staticmethod
    def update_username(user_id: int, username: str) -> bool:
        """
        根据 ID 更新用户名
        :param user_id: 用户ID
        :param username: 新的用户名
        :return: 是否成功更新了记录
        """
        if user_id is None:
            raise ValueError("更新操作需要提供 user_id")
        sql = "UPDATE user SET username = %s WHERE id = %s"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, (username, user_id))
            return affected > 0

    @staticmethod
    def delete(user_id: int) -> bool:
        """
        根据 ID 删除用户
        :param user_id: 用户ID
        :return: 是否成功删除了记录
        """
        sql = "DELETE FROM user WHERE id = %s"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, (user_id,))
            return affected > 0

    @staticmethod
    def update_password(user_id: int, new_password: str) -> bool:
        """
        根据 ID 更新用户密码
        :param user_id: 用户ID
        :param new_password: 新的密码
        :return: 是否成功更新了记录
        """
        sql = "UPDATE user SET password = %s WHERE id = %s"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, (new_password, user_id))
            return affected > 0

    @staticmethod
    def set_user_admin_status(user_id: int, is_admin: int) -> bool:
        """
        设置用户的管理员状态
        :param user_id: 用户ID
        :param is_admin: 管理员状态 (1=管理员, 0=普通用户)
        :return: 是否成功更新了记录
        """
        sql = "UPDATE user SET is_admin = %s WHERE id = %s"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, (is_admin, user_id))
            return affected > 0