from typing import List, Dict, Any

from util.db_util import get_cursor


class UserKnowledgeBaseCRUD:

    @staticmethod
    def get_knowledge_bases_by_user(user_id: int) -> List[int]:
        """
        通过用户ID查找其所有可访问的知识库ID（通过角色关联）
        :param user_id: 用户ID
        :return: 知识库ID列表
        """
        # SQL连接查询：用户 -> 角色 -> 知识库
        sql = """
        SELECT rkb.knowledge_base_id
        FROM role_user ru
        JOIN role_knowledge_base rkb ON ru.role_id = rkb.role_id
        WHERE ru.user_id = %s
        GROUP BY rkb.knowledge_base_id
        """
        with get_cursor() as cursor:
            cursor.execute(sql, (user_id,))
            rows = cursor.fetchall()
            return [row['knowledge_base_id'] for row in rows]

    @staticmethod
    def has_read_permission(user_id: int, knowledge_base_id: int) -> bool:
        return UserKnowledgeBaseCRUD._has_permission(user_id, knowledge_base_id, 0)

    @staticmethod
    def has_write_permission(user_id: int, knowledge_base_id: int) -> bool:
        return UserKnowledgeBaseCRUD._has_permission(user_id, knowledge_base_id, 1)

    @staticmethod
    def _has_permission(user_id: int, knowledge_base_id: int, required_permission: int) -> bool:
        sql = """
        SELECT MAX(rkb.permission) AS permission
        FROM role_user ru
        JOIN role_knowledge_base rkb ON ru.role_id = rkb.role_id
        WHERE ru.user_id = %s AND rkb.knowledge_base_id = %s
        """
        with get_cursor() as cursor:
            cursor.execute(sql, (user_id, knowledge_base_id))
            row = cursor.fetchone()
            return bool(row and row["permission"] is not None and row["permission"] >= required_permission)

    @staticmethod
    def get_users_by_knowledge_base(knowledge_base_id: int) -> List[Dict[str, int]]:
        """
        通过知识库ID查找所有可访问该知识库的用户ID（通过角色关联）
        :param knowledge_base_id: 知识库ID
        :return: 用户ID列表
        """
        # SQL连接查询：知识库 -> 角色 -> 用户
        sql = """
        SELECT ru.user_id, MAX(rkb.permission) AS permission
        FROM role_knowledge_base rkb
        JOIN role_user ru ON rkb.role_id = ru.role_id
        WHERE rkb.knowledge_base_id = %s
        GROUP BY ru.user_id
        """
        with get_cursor() as cursor:
            cursor.execute(sql, (knowledge_base_id,))
            rows = cursor.fetchall()
            return [{"user_id": row["user_id"], "permission": row["permission"]} for row in rows]

    @staticmethod
    def get_knowledge_bases_by_user_paged(
            user_id: int,
            page: int = 1,
            page_size: int = 10
    ) -> Dict[str, Any]:
        """
        分页查询用户可访问的知识库ID
        :param user_id: 用户ID
        :param page: 当前页码
        :param page_size: 每页数量
        :return: 分页结果字典，包含 items、total、page、page_size 键
        """
        offset = (page - 1) * page_size

        count_sql = """
                    SELECT COUNT(*) AS total
                    FROM (
                        SELECT rkb.knowledge_base_id
                        FROM role_user ru
                        JOIN role_knowledge_base rkb ON ru.role_id = rkb.role_id
                        WHERE ru.user_id = %s
                        GROUP BY rkb.knowledge_base_id
                    ) accessible_kbs
                    """

        data_sql = """
                   SELECT rkb.knowledge_base_id, MAX(rkb.permission) AS permission
                   FROM role_user ru
                            JOIN role_knowledge_base rkb ON ru.role_id = rkb.role_id
                   WHERE ru.user_id = %s
                   GROUP BY rkb.knowledge_base_id
                   LIMIT %s OFFSET %s \
                   """

        with get_cursor() as cursor:
            cursor.execute(count_sql, (user_id,))
            total = cursor.fetchone()['total']

            cursor.execute(data_sql, (user_id, page_size, offset))
            rows = cursor.fetchall()
            items = [{"knowledge_base_id": row["knowledge_base_id"], "permission": row["permission"]} for row in rows]

        return {
            "list": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }

    @staticmethod
    def get_users_by_knowledge_base_paged(knowledge_base_id: int, page: int = 1, page_size: int = 10) -> Dict[str, Any]:
        """
        分页查询可访问指定知识库的用户ID
        """
        offset = (page - 1) * page_size

        count_sql = """
                    SELECT COUNT(*) AS total
                    FROM (
                        SELECT ru.user_id
                        FROM role_knowledge_base rkb
                        JOIN role_user ru ON rkb.role_id = ru.role_id
                        WHERE rkb.knowledge_base_id = %s
                        GROUP BY ru.user_id
                    ) accessible_users
                    """

        data_sql = """
                   SELECT ru.user_id, MAX(rkb.permission) AS permission
                   FROM role_knowledge_base rkb
                            JOIN role_user ru ON rkb.role_id = ru.role_id
                   WHERE rkb.knowledge_base_id = %s
                   GROUP BY ru.user_id
                   LIMIT %s OFFSET %s \
                   """

        with get_cursor() as cursor:
            cursor.execute(count_sql, (knowledge_base_id,))
            total = cursor.fetchone()['total']

            cursor.execute(data_sql, (knowledge_base_id, page_size, offset))
            rows = cursor.fetchall()
            items = [{"user_id": row["user_id"], "permission": row["permission"]} for row in rows]

        return {
            "list": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }
