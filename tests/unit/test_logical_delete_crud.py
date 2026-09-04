from types import SimpleNamespace

from crud.announcement_crud import AnnouncementCRUD
from crud.session_crud import SessionCRUD
from crud.user_crud import UserCRUD
import crud.user_crud as user_crud
import crud.session_crud as session_crud
import crud.announcement_crud as announcement_crud


class FakeCursor:
    def __init__(self):
        self.queries = []

    def __init__(self):
        self.queries = []
        self.rowcount = 1

    def execute(self, sql, params=None):
        self.queries.append((sql, params))
        return 1

    def close(self):
        pass


class FakeConnection:
    def __init__(self):
        self.cursor_obj = FakeCursor()

    def cursor(self, *args, **kwargs):
        return self.cursor_obj

    def commit(self):
        pass

    def rollback(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        return False


def test_user_delete_is_logical(monkeypatch):
    cursor = FakeCursor()
    monkeypatch.setattr(user_crud, "get_cursor", lambda: _cursor_context(cursor))
    assert UserCRUD.delete(7) is True
    sql, params = cursor.queries[0]
    assert sql.startswith("UPDATE user SET is_deleted = 1")
    assert "deleted_at = NOW()" in sql
    assert params == (7,)


def test_session_delete_with_messages_is_single_transaction(monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr(session_crud, "get_connection", lambda: _connection_context(connection))
    assert SessionCRUD.delete_with_messages(8) is True
    assert [sql for sql, _ in connection.cursor_obj.queries] == [
        "UPDATE message SET is_deleted = 1, deleted_at = NOW() WHERE session_id = %s AND is_deleted = 0",
        "UPDATE session SET is_deleted = 1, deleted_at = NOW(), update_time = NOW() WHERE id = %s AND is_deleted = 0",
    ]


def test_announcement_delete_with_attachments_is_single_transaction(monkeypatch):
    connection = FakeConnection()
    monkeypatch.setattr(announcement_crud, "get_connection", lambda: _connection_context(connection))
    assert AnnouncementCRUD.batch_delete_with_attachments([1, 2]) == 1
    sql_text = "\n".join(sql for sql, _ in connection.cursor_obj.queries)
    assert "announcement_attachment SET is_deleted = 1" in sql_text
    assert "announcement SET is_deleted = 1" in sql_text
    assert all("DELETE FROM" not in sql for sql, _ in connection.cursor_obj.queries)


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
        return False
