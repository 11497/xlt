from typing import List, Tuple

from model.role_model import Role
from model.user_model import User
from util.db_util import get_cursor


class RoleUserCRUD:

    @staticmethod
    def batch_assign_users_to_role(role_id: int, user_ids: List[int]) -> bool:
        """
        批量分配用户到指定角色
        :param role_id: 角色ID
        :param user_ids: 用户ID列表
        :return: 是否成功分配
        """
        if not user_ids:
            return True  # 空列表视为成功操作

        # 构造批量插入SQL
        sql = "INSERT IGNORE INTO role_user (role_id, user_id) VALUES "
        values_placeholders = []
        params = []

        for user_id in user_ids:
            values_placeholders.append("(%s, %s)")
            params.extend([role_id, user_id])

        sql += ",".join(values_placeholders)

        with get_cursor() as cursor:
            affected = cursor.execute(sql, params)
            return affected > 0  # 插入操作总是返回True表示执行成功

    @staticmethod
    def batch_remove_users_from_role(role_id: int, user_ids: List[int]) -> bool:
        """
        批量从指定角色中移除用户
        :param role_id: 角色ID
        :param user_ids: 要移除的用户ID列表
        :return: 是否成功移除
        """
        if not user_ids:
            return True  # 空列表视为成功操作

        # 构造批量删除SQL
        placeholders = ','.join(['%s'] * len(user_ids))
        sql = f"DELETE FROM role_user WHERE role_id = %s AND user_id IN ({placeholders})"

        with get_cursor() as cursor:
            params = [role_id] + user_ids
            affected = cursor.execute(sql, params)
            return affected > 0  # 删除操作返回行数大于0，表示成功移除

    @staticmethod
    def get_users_by_role(role_id: int) -> List[int]:
        """
        获取指定角色下的所有用户ID
        :param role_id: 角色ID
        :return: 用户ID列表
        """
        sql = "SELECT user_id FROM role_user WHERE role_id = %s"
        with get_cursor() as cursor:
            cursor.execute(sql, (role_id,))
            rows = cursor.fetchall()
            return [row['user_id'] for row in rows]

    @staticmethod
    def get_roles_by_user(user_id: int) -> List[int]:
        """
        获取指定用户的所有角色ID
        :param user_id: 用户ID
        :return: 角色ID列表
        """
        sql = "SELECT role_id FROM role_user WHERE user_id = %s"
        with get_cursor() as cursor:
            cursor.execute(sql, (user_id,))
            rows = cursor.fetchall()
            return [row['role_id'] for row in rows]

    @staticmethod
    def assign_user_to_role(role_id: int, user_id: int) -> bool:
        """
        分配单个用户到指定角色
        :param role_id: 角色ID
        :param user_id: 用户ID
        :return: 是否成功分配
        """
        sql = "INSERT IGNORE INTO role_user (role_id, user_id) VALUES (%s, %s)"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, (role_id, user_id))
            return affected > 0

    @staticmethod
    def remove_user_from_role(role_id: int, user_id: int) -> bool:
        """
        从指定角色中移除单个用户
        :param role_id: 角色ID
        :param user_id: 用户ID
        :return: 是否成功移除
        """
        sql = "DELETE FROM role_user WHERE role_id = %s AND user_id = %s"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, (role_id, user_id))
            return affected > 0

    @staticmethod
    def delete_by_role(role_id: int) -> bool:
        """
        删除指定角色的所有用户关联关系
        :param role_id: 角色ID
        :return: 是否成功删除
        """
        sql = "DELETE FROM role_user WHERE role_id = %s"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, (role_id,))
            return affected > 0

    @staticmethod
    def delete_by_user(user_id: int) -> bool:
        """
        删除指定用户的所有角色关联关系
        :param user_id: 用户ID
        :return: 是否成功删除
        """
        sql = "DELETE FROM role_user WHERE user_id = %s"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, (user_id,))
            return affected > 0

    @staticmethod
    def get_page_users_by_role(
            role_id: int,
            page: int = 1,
            page_size: int = 10
    ) -> Tuple[List[User], int]:
        """
        按角色分页查询关联的用户
        :param role_id: 角色ID
        :param page: 页码（从1开始）
        :param page_size: 每页条数
        :return: (用户列表, 总记录数)
        """
        offset = (page - 1) * page_size

        sql_count = ("SELECT COUNT(*) AS total FROM role_user ru "
                     "JOIN user u ON ru.user_id = u.id "
                     "WHERE ru.role_id = %s")
        sql_data = ("SELECT u.* FROM role_user ru "
                    "JOIN user u ON ru.user_id = u.id "
                    "WHERE ru.role_id = %s "
                    "LIMIT %s OFFSET %s")

        with get_cursor() as cursor:
            cursor.execute(sql_count, (role_id,))
            count_row = cursor.fetchone()
            if isinstance(count_row, dict):
                total = int(count_row.get("total", count_row.get("COUNT(*)", 0)))
            else:
                total = int(count_row[0]) if count_row else 0

            cursor.execute(sql_data, (role_id, page_size, offset))
            rows = cursor.fetchall()
            users = [User.from_row(r) for r in rows]

        return users, total

    @staticmethod
    def get_page_roles_by_user(
            user_id: int,
            page: int = 1,
            page_size: int = 10
    ) -> Tuple[List[Role], int]:
        """
        按用户分页查询关联的角色
        :param user_id: 用户ID
        :param page: 页码（从1开始）
        :param page_size: 每页条数
        :return: (角色列表, 总记录数)
        """
        offset = (page - 1) * page_size

        sql_count = ("SELECT COUNT(*) AS total FROM role_user ru "
                     "JOIN role r ON ru.role_id = r.id "
                     "WHERE ru.user_id = %s")
        sql_data = ("SELECT r.* FROM role_user ru "
                    "JOIN role r ON ru.role_id = r.id "
                    "WHERE ru.user_id = %s "
                    "LIMIT %s OFFSET %s")

        with get_cursor() as cursor:
            cursor.execute(sql_count, (user_id,))
            count_row = cursor.fetchone()
            if isinstance(count_row, dict):
                total = int(count_row.get("total", count_row.get("COUNT(*)", 0)))
            else:
                total = int(count_row[0]) if count_row else 0

            cursor.execute(sql_data, (user_id, page_size, offset))
            rows = cursor.fetchall()
            roles = [Role.from_row(r) for r in rows]

        return roles, total