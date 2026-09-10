import asyncio
import re

import pytest

from crud.announcement_crud import AnnouncementCRUD
from crud.knowledge_base_crud import KnowledgeBaseCRUD
from crud.role_crud import RoleCRUD
from crud.session_crud import SessionCRUD
from crud.user_crud import UserCRUD
from crud.user_knowledge_base_crud import UserKnowledgeBaseCRUD
import crud.announcement_crud as announcement_crud
import crud.knowledge_base_crud as knowledge_base_crud
import crud.role_crud as role_crud
import crud.session_crud as session_crud
import crud.user_crud as user_crud
from crud.role_knowledge_base_crud import RoleKnowledgeBaseCRUD
from crud.role_user_crud import RoleUserCRUD
import crud.role_knowledge_base_crud as role_knowledge_base_crud
import crud.role_user_crud as role_user_crud
from model.user_model import User
import router.knowledge_base_router as knowledge_base_router
from router.knowledge_base_router import delete_knowledge_base


class FakeCursor:
    def __init__(self):
        self.queries = []
        self.rowcount = 1
        self.fetchone_result = None
        self.fetchall_result = []

    def execute(self, sql, params=None):
        self.queries.append((sql, params))
        return 1

    def fetchone(self):
        return self.fetchone_result

    def fetchall(self):
        return self.fetchall_result

    def close(self):
        pass


_TOMBSTONE_SUFFIX = re.compile(r"^[0-9a-f]{32}$")


def _assert_tombstone_name(new_name: str, original: str) -> None:
    prefix = f"{original}__"
    assert new_name.startswith(prefix)
    suffix = new_name[len(prefix):]
    assert _TOMBSTONE_SUFFIX.fullmatch(suffix)
    assert len(new_name) > 15


class FakeConnection:
    def __init__(self):
        self.cursor_obj = FakeCursor()
        self.committed = False
        self.rolled_back = False

    def cursor(self, *args, **kwargs):
        return self.cursor_obj

    def commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        if exc is None:
            self.commit()
        else:
            self.rollback()
        return False


def test_user_delete_is_logical(monkeypatch):
    cursor = FakeCursor()
    cursor.fetchone_result = {"username": "alice"}
    monkeypatch.setattr(user_crud, "get_cursor", lambda: _cursor_context(cursor))
    assert UserCRUD.delete(7) is True
    assert len(cursor.queries) == 2
    select_sql, select_params = cursor.queries[0]
    update_sql, update_params = cursor.queries[1]
    assert "SELECT username FROM user" in select_sql
    assert select_params == (7,)
    assert "username = %s" in update_sql
    assert "is_deleted = 1" in update_sql
    assert "deleted_at = NOW()" in update_sql
    new_name, user_id = update_params
    assert user_id == 7
    _assert_tombstone_name(new_name, "alice")


def test_user_delete_skips_already_deleted(monkeypatch):
    cursor = FakeCursor()
    cursor.fetchone_result = None
    monkeypatch.setattr(user_crud, "get_cursor", lambda: _cursor_context(cursor))
    assert UserCRUD.delete(7) is False
    assert len(cursor.queries) == 1
    assert "UPDATE user" not in cursor.queries[0][0]


def test_role_delete_renames_unique_name(monkeypatch):
    cursor = FakeCursor()
    cursor.fetchone_result = {"name": "teacher"}
    monkeypatch.setattr(role_crud, "get_cursor", lambda: _cursor_context(cursor))
    assert RoleCRUD.delete(4) is True
    update_sql, update_params = cursor.queries[1]
    assert "name = %s" in update_sql
    assert "is_deleted = 1" in update_sql
    assert "deleted_at = NOW()" in update_sql
    new_name, role_id = update_params
    assert role_id == 4
    _assert_tombstone_name(new_name, "teacher")


def test_knowledge_base_crud_delete_renames_unique_name(monkeypatch):
    cursor = FakeCursor()
    cursor.fetchone_result = {"name": "campus"}
    monkeypatch.setattr(knowledge_base_crud, "get_cursor", lambda: _cursor_context(cursor))
    assert KnowledgeBaseCRUD.delete(9) is True
    update_sql, update_params = cursor.queries[1]
    assert "name = %s" in update_sql
    assert "is_deleted = 1" in update_sql
    assert "deleted_at = NOW()" in update_sql
    new_name, kb_id = update_params
    assert kb_id == 9
    _assert_tombstone_name(new_name, "campus")


def test_session_delete_with_messages_is_single_transaction(monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr(session_crud, "get_connection", lambda: _connection_context(connection))
    assert SessionCRUD.delete_with_messages(8) is True
    assert [sql for sql, _ in connection.cursor_obj.queries] == [
        "UPDATE message_source SET is_deleted = 1, deleted_at = NOW() WHERE session_id = %s AND is_deleted = 0",
        "UPDATE message SET is_deleted = 1, deleted_at = NOW() WHERE session_id = %s AND is_deleted = 0",
        "UPDATE session SET is_deleted = 1, deleted_at = NOW(), update_time = NOW() WHERE id = %s AND is_deleted = 0",
    ]
    assert connection.committed is True
    assert connection.rolled_back is False


def test_announcement_delete_with_attachments_is_single_transaction(monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr(announcement_crud, "get_connection", lambda: _connection_context(connection))
    assert AnnouncementCRUD.batch_delete_with_attachments([1, 2]) == 1
    sql_text = "\n".join(sql for sql, _ in connection.cursor_obj.queries)
    assert "announcement_attachment SET is_deleted = 1" in sql_text
    assert "announcement SET is_deleted = 1" in sql_text
    assert all("DELETE FROM" not in sql for sql, _ in connection.cursor_obj.queries)
    assert connection.committed is True


def test_session_delete_rolls_back_when_second_update_fails(monkeypatch):
    connection = FakeConnection()

    def execute(sql, params=None):
        connection.cursor_obj.queries.append((sql, params))
        if "UPDATE session" in sql:
            raise RuntimeError("数据库写入失败")
        return 1

    connection.cursor_obj.execute = execute
    monkeypatch.setattr(session_crud, "get_connection", lambda: _connection_context(connection))
    with pytest.raises(RuntimeError):
        SessionCRUD.delete_with_messages(8)
    assert connection.rolled_back is True
    assert connection.committed is False


def test_role_knowledge_base_binding_query_filters_deleted_role(monkeypatch):
    class Cursor(FakeCursor):
        def fetchall(self):
            return []

    cursor = Cursor()
    monkeypatch.setattr(role_knowledge_base_crud, "get_cursor", lambda: _cursor_context(cursor))
    assert RoleKnowledgeBaseCRUD.get_roles_by_knowledge_base(3) == []
    assert "JOIN role r" in cursor.queries[0][0]
    assert "r.is_deleted = 0" in cursor.queries[0][0]
    assert "rkb.is_deleted = 0" in cursor.queries[0][0]


def test_role_user_assignment_sql_filters_deleted_entities(monkeypatch):
    cursor = FakeCursor()
    monkeypatch.setattr(role_user_crud, "get_cursor", lambda: _cursor_context(cursor))
    assert RoleUserCRUD.assign_user_to_role(1, 2) is True
    sql, params = cursor.queries[0]
    assert "FROM role r CROSS JOIN user u" in sql
    assert "r.is_deleted = 0" in sql
    assert "u.is_deleted = 0" in sql
    assert params == (1, 2, 1, 2)


class _cursor_context:
    def __init__(self, cursor):
        self.cursor = cursor

    def __enter__(self):
        return self.cursor

    def __exit__(self, exc_type, exc, traceback):
        return False


class _connection_context:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc, traceback):
        return self.connection.__exit__(exc_type, exc, traceback)


def test_permission_query_filters_deleted_role_user_binding(monkeypatch):
    import crud.user_knowledge_base_crud as user_knowledge_base_crud

    class Cursor(FakeCursor):
        def fetchone(self):
            return None

        def fetchall(self):
            return []

    cursor = Cursor()
    monkeypatch.setattr(
        user_knowledge_base_crud,
        "get_cursor",
        lambda: _cursor_context(cursor),
    )
    assert UserKnowledgeBaseCRUD.has_read_permission(2, 3) is False
    sql = cursor.queries[0][0]
    assert "ru.is_deleted = 0" in sql
    assert "rkb.is_deleted = 0" in sql


def test_role_user_query_filters_deleted_role(monkeypatch):
    class Cursor(FakeCursor):
        def fetchall(self):
            return []

    cursor = Cursor()
    monkeypatch.setattr(role_user_crud, "get_cursor", lambda: _cursor_context(cursor))
    assert RoleUserCRUD.get_users_by_role(3) == []
    sql = cursor.queries[0][0]
    assert "JOIN role r" in sql
    assert "r.is_deleted = 0" in sql
    assert "ru.is_deleted = 0" in sql


def test_role_knowledge_base_query_filters_deleted_knowledge_base(monkeypatch):
    class Cursor(FakeCursor):
        def fetchall(self):
            return []

    cursor = Cursor()
    monkeypatch.setattr(role_knowledge_base_crud, "get_cursor", lambda: _cursor_context(cursor))
    assert RoleKnowledgeBaseCRUD.get_roles_by_knowledge_base(3) == []
    sql = cursor.queries[0][0]
    assert "JOIN knowledge_base kb" in sql
    assert "kb.is_deleted = 0" in sql
    assert "rkb.is_deleted = 0" in sql


class SequentialCursor:
    def __init__(self, fetchone_results, fetchall_results=None):
        self.queries = []
        self.fetchone_results = list(fetchone_results)
        self.fetchall_results = list(fetchall_results or [])

    def execute(self, sql, params=None):
        self.queries.append((sql, params))
        return 1

    def fetchone(self):
        if self.fetchone_results:
            return self.fetchone_results.pop(0)
        return None

    def fetchall(self):
        if self.fetchall_results:
            return self.fetchall_results.pop(0)
        return []

    def close(self):
        pass


def test_knowledge_base_router_delete_renames_unique_name(monkeypatch):
    connection = FakeConnection()
    cursor = SequentialCursor(
        fetchone_results=[{"id": 5, "name": "campus"}, None, None],
        fetchall_results=[[], []],
    )
    connection.cursor_obj = cursor
    monkeypatch.setattr(knowledge_base_router, "get_connection", lambda: connection)

    admin = User(id=1, username="admin1", password="secret1", is_admin=1)
    result = asyncio.run(delete_knowledge_base(id=5, _admin=admin))

    assert result["code"] == 1
    update_sql, update_params = next(
        (sql, params)
        for sql, params in cursor.queries
        if sql.strip().startswith("UPDATE knowledge_base")
    )
    assert "name = %s" in update_sql
    assert "is_deleted = 1" in update_sql
    assert "deleted_at = NOW()" in update_sql
    new_name, kb_id = update_params
    assert kb_id == 5
    _assert_tombstone_name(new_name, "campus")
    assert connection.committed is True
    assert connection.rolled_back is False
