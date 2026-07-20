from typing import List, Optional, Tuple
from util.db_util import get_cursor
from model.role_model import Role


class RoleCRUD:

    @staticmethod
    def create(role: Role) -> int:
        """
        新增角色
        :param role: 角色对象
        :return: 新插入记录的 id
        """
        sql = "INSERT INTO role (name) VALUES (%s)"
        with get_cursor() as cursor:
            cursor.execute(sql, (role.name,))
            return cursor.lastrowid

    @staticmethod
    def get_by_name(name: str) -> Optional[Role]:
        """
        根据 name 查询单个角色
        :param name: 角色名
        :return: 角色对象（如果存在）
        """
        sql = "SELECT * FROM role WHERE name = %s"
        with get_cursor() as cursor:
            cursor.execute(sql, (name,))
            row = cursor.fetchone()
            return Role.from_row(row) if row else None

    @staticmethod
    def get_by_id(role_id: int) -> Optional[Role]:
        """
        根据 ID 查询单个角色
        :param role_id: 角色ID
        :return: 角色对象（如果存在）
        """
        sql = "SELECT * FROM role WHERE id = %s"
        with get_cursor() as cursor:
            cursor.execute(sql, (role_id,))
            row = cursor.fetchone()
            return Role.from_row(row) if row else None

    @staticmethod
    def get_all() -> List[Role]:
        """
        查询所有角色
        :return: 角色对象列表
        """
        sql = "SELECT * FROM role"
        with get_cursor() as cursor:
            cursor.execute(sql)
            rows = cursor.fetchall()
            return [Role.from_row(r) for r in rows]

    @staticmethod
    def get_page(page: int = 1, page_size: int = 10) -> Tuple[List[Role], int]:
        """
        分页查询角色
        :param page: 页码（从1开始）
        :param page_size: 每页条数
        :return: (角色列表, 总记录数)
        """
        offset = (page - 1) * page_size

        sql_count = "SELECT COUNT(*) AS total FROM role"
        sql_data = "SELECT * FROM role LIMIT %s OFFSET %s"

        with get_cursor() as cursor:
            # 获取总数，兼容字典游标和元组游标
            cursor.execute(sql_count)
            count_row = cursor.fetchone()
            if isinstance(count_row, dict):
                total = int(count_row.get("total", count_row.get("COUNT(*)", 0)))
            else:
                total = int(count_row[0]) if count_row else 0

            # 获取分页数据
            cursor.execute(sql_data, (page_size, offset))
            rows = cursor.fetchall()
            roles = [Role.from_row(r) for r in rows]

        return roles, total

    @staticmethod
    def update_name(role_id: int, name: str) -> bool:
        """
        根据 ID 更新角色名
        :param role_id: 角色ID
        :param name: 新的角色名
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
        :param role_id: 角色ID
        :return: 是否成功删除了记录
        """
        sql = "DELETE FROM role WHERE id = %s"
        with get_cursor() as cursor:
            affected = cursor.execute(sql, (role_id,))
            return affected > 0

    @staticmethod
    def search(content: str) -> List[Role]:
        """
        搜索角色
        :param content: 搜索内容（角色名或ID）
        :return: 角色对象列表
        """
        roles = []

        sql1 = "SELECT * FROM role WHERE id = %s"
        with get_cursor() as cursor:
            cursor.execute(sql1, (content,))
            rows = cursor.fetchall()
            roles.extend([Role.from_row(r) for r in rows])

        sql2 = "SELECT * FROM role WHERE name LIKE %s"
        with get_cursor() as cursor:
            cursor.execute(sql2, (f"%{content}%",))
            rows = cursor.fetchall()
            roles.extend([Role.from_row(r) for r in rows])

        return roles
