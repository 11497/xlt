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
        SELECT DISTINCT rkb.knowledge_base_id
        FROM role_user ru
        JOIN role_knowledge_base rkb ON ru.role_id = rkb.role_id
        WHERE ru.user_id = %s
        """
        with get_cursor() as cursor:
            cursor.execute(sql, (user_id,))
            rows = cursor.fetchall()
            return [row['knowledge_base_id'] for row in rows]

    @staticmethod
    def get_users_by_knowledge_base(knowledge_base_id: int) -> List[int]:
        """
        通过知识库ID查找所有可访问该知识库的用户ID（通过角色关联）
        :param knowledge_base_id: 知识库ID
        :return: 用户ID列表
        """
        # SQL连接查询：知识库 -> 角色 -> 用户
        sql = """
        SELECT DISTINCT ru.user_id
        FROM role_knowledge_base rkb
        JOIN role_user ru ON rkb.role_id = ru.role_id
        WHERE rkb.knowledge_base_id = %s
        """
        with get_cursor() as cursor:
            cursor.execute(sql, (knowledge_base_id,))
            rows = cursor.fetchall()
            return [row['user_id'] for row in rows]

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
                    SELECT COUNT(DISTINCT rkb.knowledge_base_id) as total
                    FROM role_user ru
                             JOIN role_knowledge_base rkb ON ru.role_id = rkb.role_id
                    WHERE ru.user_id = %s \
                    """

        data_sql = """
                   SELECT DISTINCT rkb.knowledge_base_id
                   FROM role_user ru
                            JOIN role_knowledge_base rkb ON ru.role_id = rkb.role_id
                   WHERE ru.user_id = %s
                   LIMIT %s OFFSET %s \
                   """

        with get_cursor() as cursor:
            cursor.execute(count_sql, (user_id,))
            total = cursor.fetchone()['total']

            cursor.execute(data_sql, (user_id, page_size, offset))
            rows = cursor.fetchall()
            items = [row['knowledge_base_id'] for row in rows]

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
                    SELECT COUNT(DISTINCT ru.user_id) as total
                    FROM role_knowledge_base rkb
                             JOIN role_user ru ON rkb.role_id = ru.role_id
                    WHERE rkb.knowledge_base_id = %s \
                    """

        data_sql = """
                   SELECT DISTINCT ru.user_id
                   FROM role_knowledge_base rkb
                            JOIN role_user ru ON rkb.role_id = ru.role_id
                   WHERE rkb.knowledge_base_id = %s
                   LIMIT %s OFFSET %s \
                   """

        with get_cursor() as cursor:
            cursor.execute(count_sql, (knowledge_base_id,))
            total = cursor.fetchone()['total']

            cursor.execute(data_sql, (knowledge_base_id, page_size, offset))
            rows = cursor.fetchall()
            items = [row['user_id'] for row in rows]

        return {
            "list": items,
            "total": total,
            "page": page,
            "page_size": page_size
        }