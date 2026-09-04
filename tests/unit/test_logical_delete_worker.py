import json
from types import SimpleNamespace

import pytest

import ai.indexing_worker as indexing_worker
from crud.document_crud import DocumentCRUD
from crud.document_task_crud import DocumentTaskCRUD


class FakeCursor:
    def __init__(self):
        self.queries = []
        self.rowcount = 1

    def execute(self, sql, params=None):
        self.queries.append((sql, params))

    def close(self):
        pass


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


def make_task(task_id=11, document_id=22, kb_id=3):
    return SimpleNamespace(
        id=task_id,
        document_id=document_id,
        knowledge_base_id=kb_id,
        task_type="delete",
        payload=json.dumps({"object_key": "knowledge_base/3/x.txt", "filename": "x.txt"}),
        retry_count=0,
        max_retries=5,
    )


def test_delete_task_does_not_delete_oss(monkeypatch):
    monkeypatch.setattr(
        indexing_worker,
        "IngestionService",
        lambda: SimpleNamespace(delete_document=lambda *_: {"chroma": True, "es": True}),
    )
    monkeypatch.setattr(DocumentCRUD, "update_status", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(DocumentTaskCRUD, "mark_retry", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(indexing_worker.OSSUtil, "delete_file", lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("OSS 不应被删除")))

    connection = FakeConnection()
    monkeypatch.setattr(indexing_worker, "get_connection", lambda: connection)

    indexing_worker._handle_delete_task(11, 22, 3, {"object_key": "x"})

    sql_text = "\n".join(sql for sql, _ in connection.cursor_obj.queries)
    assert "DELETE FROM" not in sql_text
    assert "is_deleted = 1" in sql_text
    assert any(isinstance(params, tuple) and params and isinstance(params[0], str) and "oss_retained" in params[0] for _, params in connection.cursor_obj.queries)
    assert connection.committed is True


@pytest.mark.parametrize(
    "result,expected_failed",
    [
        ({"chroma": False, "es": True}, "chroma"),
        ({"chroma": True, "es": False}, "es"),
        ({"chroma": False, "es": False}, "chroma,es"),
    ],
)
def test_delete_task_retries_while_backend_fails(monkeypatch, result, expected_failed):
    monkeypatch.setattr(
        indexing_worker,
        "IngestionService",
        lambda: SimpleNamespace(delete_document=lambda *_args: result),
    )

    connection = FakeConnection()
    monkeypatch.setattr(indexing_worker, "get_connection", lambda: connection)

    with pytest.raises(RuntimeError, match=expected_failed):
        indexing_worker._handle_delete_task(11, 22, 3, {})

    assert not connection.committed
    assert all("is_deleted = 1" not in sql for sql, _ in connection.cursor_obj.queries)
