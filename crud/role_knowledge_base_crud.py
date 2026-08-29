from typing import List, Any

from model.knowledge_base_model import KnowledgeBase
from model.role_model import Role
from util.db_util import get_cursor


class RoleKnowledgeBaseCRUD:

    @staticmethod
    def batch_assign_roles_to_knowledge_base(knowledge_base_id: int, bindings: List[dict]) -> bool:
        """
        批量分配角色到指定知识库
        :param knowledge_base_id: 知识库ID
        :param bindings: 包含 role_id 和 permission 的绑定列表
        :return: 是否成功分配
        """
        if not bindings:
            return True

        sql = ("INSERT INTO role_knowledge_base (role_id, knowledge_base_id, permission) "
               "VALUES (%s, %s, %s) "
               "ON DUPLICATE KEY UPDATE permission = VALUES(permission)")
        params = [(item["role_id"], knowledge_base_id, item["permission"]) for item in bindings]

        with get_cursor() as cursor:
            cursor.executemany(sql, params)
            return True

    @staticmethod
    def batch_remove_roles_from_knowledge_base(knowledge_base_id: int, role_ids: List[int]) -> bool:
        """
        批量从指定知识库中删除角色
        :param knowledge_base_id: 知识库ID
        :param role_ids: 要删除的角色ID列表
        :return: 是否成功删除
        """
        if not role_ids:
            return True  # 空列表视为成功操作
        # 构造批量删除SQL
        placeholders = ','.join(['%s'] * len(role_ids))
        sql = f"DELETE FROM role_knowledge_base WHERE knowledge_base_id = %s AND role_id IN ({placeholders})"
        with get_cursor() as cursor:
            params = [knowledge_base_id] + role_ids
            cursor.execute(sql, params)
            return True

    @staticmethod
    def get_roles_by_knowledge_base(knowledge_base_id: int) -> List[int]:
        """
        获取指定知识库的所有角色ID
        :param knowledge_base_id: 知识库ID
        :return: 角色ID列表
        """
        sql = "SELECT role_id FROM role_knowledge_base WHERE knowledge_base_id = %s"
        with get_cursor() as cursor:
            cursor.execute(sql, (knowledge_base_id,))
            rows = cursor.fetchall()
            return [row['role_id'] for row in rows]

    @staticmethod
    def get_knowledge_base_by_role(role_id: int) -> List[int]:
        """
        获取指定角色下的所有知识库ID
        :param role_id: 角色ID
        :return: 知识库ID列表
        """
        sql = "SELECT knowledge_base_id FROM role_knowledge_base WHERE role_id = %s"
        with get_cursor() as cursor:
            cursor.execute(sql, (role_id,))
            rows = cursor.fetchall()
            return [row['knowledge_base_id'] for row in rows]

    @staticmethod
    def assign_knowledge_base_to_role(role_id: int, knowledge_base_id: int) -> bool:
        """
        分配单个知识库到指定角色
        :param role_id: 角色ID
        :param knowledge_base_id: 知识库ID
        :return: 是否成功分配
        """
        return RoleKnowledgeBaseCRUD.upsert_binding(role_id, knowledge_base_id, 0)

    @staticmethod
    def upsert_binding(role_id: int, knowledge_base_id: int, permission: int) -> bool:
        """新增绑定或更新已有绑定的权限。"""
        sql = ("INSERT INTO role_knowledge_base (role_id, knowledge_base_id, permission) "
               "VALUES (%s, %s, %s) "
               "ON DUPLICATE KEY UPDATE permission = VALUES(permission)")
        with get_cursor() as cursor:
            cursor.execute(sql, (role_id, knowledge_base_id, permission))
            return True

    @staticmethod
    def remove_knowledge_base_from_role(role_id: int, knowledge_base_id: int) -> bool:
        """
        从指定角色中移除单个知识库
        :param role_id: 角色ID
        :param knowledge_base_id: 知识库ID
        :return: 是否成功移除
        """
        sql = "DELETE FROM role_knowledge_base WHERE role_id = %s AND knowledge_base_id = %s"
        with get_cursor() as cursor:
            cursor.execute(sql, (role_id, knowledge_base_id))
            return True

    @staticmethod
    def delete_by_role(role_id: int) -> bool:
        """
        删除指定角色的所有知识库关联关系
        :param role_id: 角色ID
        :return: 是否成功删除
        """
        sql = "DELETE FROM role_knowledge_base WHERE role_id = %s"
        with get_cursor() as cursor:
            cursor.execute(sql, (role_id,))
            return True

    @staticmethod
    def delete_by_knowledge_base(knowledge_base_id: int) -> bool:
        """
        删除指定知识库的所有角色关联关系
        :param knowledge_base_id: 知识库ID
        :return: 是否成功删除
        """
        sql = "DELETE FROM role_knowledge_base WHERE knowledge_base_id = %s"
        with get_cursor() as cursor:
            cursor.execute(sql, (knowledge_base_id,))
            return True

    @staticmethod
    def get_page_knowledge_base_by_role(
            role_id: int,
            page: int = 1,
            page_size: int = 10
    ) -> tuple[list[KnowledgeBase], int | Any]:
        """
        按角色分页查询关联的知识库
        :param role_id: 角色ID
        :param page: 页码（从1开始）
        :param page_size: 每页条数
        :return: (知识库列表, 总记录数)
        """
        offset = (page - 1) * page_size

        sql_count = ("SELECT COUNT(*) AS total FROM role_knowledge_base rkb "
                     "JOIN knowledge_base kb ON rkb.knowledge_base_id = kb.id "
                     "WHERE rkb.role_id = %s")
        sql_data = ("SELECT kb.id, kb.name, rkb.permission FROM role_knowledge_base rkb "
                    "JOIN knowledge_base kb ON rkb.knowledge_base_id = kb.id "
                    "WHERE rkb.role_id = %s "
                    "LIMIT %s OFFSET %s")

        with get_cursor() as cursor:
            cursor.execute(sql_count, (role_id,))
            count_row = cursor.fetchone()
            if isinstance(count_row, dict):
                total = count_row.get("total", count_row.get("COUNT(*)", 0))
            else:
                total = count_row[0] if count_row else 0

            cursor.execute(sql_data, (role_id, page_size, offset))
            rows = cursor.fetchall()
            knowledge_bases = [
                {"id": r["id"], "name": r["name"], "permission": r["permission"]}
                for r in rows
            ]

        return knowledge_bases, total

    @staticmethod
    def get_page_roles_by_knowledge_base(
            knowledge_base_id: int,
            page: int = 1,
            page_size: int = 10
    ) -> tuple[list[Role], int | Any]:
        """
        按知识库分页查询关联的角色
        :param knowledge_base_id: 知识库ID
        :param page: 页码（从1开始）
        :param page_size: 每页条数
        :return: (角色列表, 总记录数)
        """
        offset = (page - 1) * page_size

        sql_count = ("SELECT COUNT(*) AS total FROM role_knowledge_base rkb "
                     "JOIN role r ON rkb.role_id = r.id "
                     "WHERE rkb.knowledge_base_id = %s")
        sql_data = ("SELECT r.id, r.name, rkb.permission FROM role_knowledge_base rkb "
                    "JOIN role r ON rkb.role_id = r.id "
                    "WHERE rkb.knowledge_base_id = %s "
                    "LIMIT %s OFFSET %s")

        with get_cursor() as cursor:
            cursor.execute(sql_count, (knowledge_base_id,))
            count_row = cursor.fetchone()
            if isinstance(count_row, dict):
                total = count_row.get("total", count_row.get("COUNT(*)", 0))
            else:
                total = count_row[0] if count_row else 0

            cursor.execute(sql_data, (knowledge_base_id, page_size, offset))
            rows = cursor.fetchall()
            roles = [
                {"id": r["id"], "name": r["name"], "permission": r["permission"]}
                for r in rows
            ]

        return roles, total
