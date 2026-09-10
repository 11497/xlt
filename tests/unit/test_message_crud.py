from datetime import datetime
from types import SimpleNamespace

from crud.message_crud import MessageCRUD
from model.message_model import Message


class CursorContext:
    def __init__(self, cursor):
        self.cursor = cursor

    def __enter__(self):
        return self.cursor

    def __exit__(self, *_args):
        return False


def test_create_malicious_pair_uses_one_multi_row_insert(monkeypatch):
    cursor = SimpleNamespace(lastrowid=101)
    queries = []
    cursor.execute = lambda sql, params: queries.append((sql, params))
    cursor.fetchall = lambda: [{"id": 101}, {"id": 103}]
    monkeypatch.setattr(
        "crud.message_crud.get_cursor",
        lambda: CursorContext(cursor),
    )
    now = datetime.now()
    user_message = Message(
        session_id=7,
        role="user",
        content="恶意输入",
        create_time=now,
        is_malicious=1,
    )
    assistant_message = Message(
        session_id=7,
        role="assistant",
        content="对话包含恶意或敏感内容",
        create_time=now,
    )

    ids = MessageCRUD.create_malicious_pair(user_message, assistant_message)

    assert ids == (101, 103)
    assert len(queries) == 2
    sql, params = queries[0]
    assert sql.count("(%s, %s, %s, %s, %s, %s, %s)") == 2
    assert params[1:6] == ("user", "恶意输入", None, 1, 0)
    assert params[8:13] == ("assistant", "对话包含恶意或敏感内容", None, 0, 0)
    assert params[6] == params[13]
    assert "ORDER BY id LIMIT 2" in queries[1][0]


def test_get_by_session_id_uses_stable_order(monkeypatch):
    cursor = SimpleNamespace()
    queries = []
    cursor.execute = lambda sql, params: queries.append((sql, params))
    cursor.fetchall = lambda: []
    monkeypatch.setattr(
        "crud.message_crud.get_cursor",
        lambda: CursorContext(cursor),
    )

    assert MessageCRUD.get_by_session_id(7) == []
    assert "ORDER BY create_time, id" in queries[0][0]
