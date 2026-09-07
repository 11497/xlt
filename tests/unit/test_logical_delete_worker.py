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
        self.fetch_results = []

    def execute(self, sql, params=None):
        self.queries.append((sql, params))

    def fetchone(self):
        if self.fetch_results:
            return self.fetch_results.pop(0)
        return None

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
    connection.cursor_obj.fetch_results = [
        {"id": 3},
        {"id": 22},
        {"id": 11},
    ]
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
    connection.cursor_obj.fetch_results = [
        {"id": 7},
        {"id": 31},
    ]
    monkeypatch.setattr(indexing_worker, "get_connection", lambda: connection)

    with pytest.raises(RuntimeError, match=expected_failed):
        indexing_worker._handle_delete_task(11, 22, 3, {})

    assert not connection.committed
    assert all("is_deleted = 1" not in sql for sql, _ in connection.cursor_obj.queries)

def test_delete_kb_task_success_soft_deletes_documents_kb_and_task(monkeypatch):
    monkeypatch.setattr(
        indexing_worker,
        "IngestionService",
        lambda: SimpleNamespace(
            delete_knowledge_base=lambda *_: {"chroma": True, "es": True}
        ),
    )
    monkeypatch.setattr(
        indexing_worker.OSSUtil,
        "delete_file",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("OSS 不应被删除")),
    )

    connection = FakeConnection()
    connection.cursor_obj.fetch_results = [
        {"id": 7},
        {"id": 31},
    ]
    monkeypatch.setattr(indexing_worker, "get_connection", lambda: connection)
    indexing_worker._handle_delete_kb_task(31, 7, {"kb_id": 7})

    sql_text = "\n".join(sql for sql, _ in connection.cursor_obj.queries)
    assert "UPDATE document SET status = 'deleted'" in sql_text
    assert "WHERE knowledge_base_id = %s AND is_deleted = 0 AND status = 'deleting'" in sql_text
    assert "UPDATE knowledge_base SET is_deleted = 1" in sql_text
    kb_updates = [sql for sql, _ in connection.cursor_obj.queries if "UPDATE knowledge_base" in sql]
    assert kb_updates
    assert all("name" not in sql for sql in kb_updates)
    assert "UPDATE document_task SET status = 'done'" in sql_text
    assert "DELETE FROM" not in sql_text
    assert any(isinstance(params, tuple) and "oss_retained" in str(params) for _, params in connection.cursor_obj.queries)
    assert connection.committed is True
    assert connection.rolled_back is False


def test_delete_kb_task_retries_when_either_backend_fails(monkeypatch):
    result = {"chroma": True, "es": False}
    monkeypatch.setattr(
        indexing_worker,
        "IngestionService",
        lambda: SimpleNamespace(delete_knowledge_base=lambda *_: result),
    )

    with pytest.raises(RuntimeError, match="es"):
        indexing_worker._handle_delete_kb_task(31, 7, {"kb_id": 7})


def test_delete_kb_final_transaction_rolls_back_all_updates(monkeypatch):
    monkeypatch.setattr(
        indexing_worker,
        "IngestionService",
        lambda: SimpleNamespace(
            delete_knowledge_base=lambda *_: {"chroma": True, "es": True}
        ),
    )
    connection = FakeConnection()
    connection.cursor_obj.fetch_results = [
        {"id": 7},
        {"id": 31},
    ]

    def execute(sql, params=None):
        connection.cursor_obj.queries.append((sql, params))
        if "UPDATE document_task" in sql:
            raise RuntimeError("数据库写入失败")
        return 1

    connection.cursor_obj.execute = execute
    monkeypatch.setattr(indexing_worker, "get_connection", lambda: connection)

    with pytest.raises(RuntimeError):
        indexing_worker._handle_delete_kb_task(31, 7, {"kb_id": 7})

    assert connection.rolled_back is True
    assert connection.committed is False
    sql_text = "\n".join(sql for sql, _ in connection.cursor_obj.queries)
    assert "UPDATE document SET status = 'deleted'" in sql_text
    assert "UPDATE knowledge_base SET is_deleted = 1" in sql_text
    assert "UPDATE document_task SET status = 'done'" in sql_text


def test_validate_index_task_skips_document_deleting(monkeypatch):
    connection = FakeConnection()
    connection.cursor_obj.fetch_results = [{"id": 3}, {"id": 22, "status": "deleting"}]
    monkeypatch.setattr(indexing_worker, "get_connection", lambda: connection)

    assert indexing_worker._validate_index_task(41, 22, 3) is False

    sql_text = "\n".join(sql for sql, _ in connection.cursor_obj.queries)
    assert "UPDATE document_task SET status = 'done'" in sql_text
    assert any(
        isinstance(params, tuple)
        and '"skipped": "document_deleting"' in str(params[0])
        for _, params in connection.cursor_obj.queries
    )
    assert connection.committed is True
    assert connection.rolled_back is False


def test_handle_index_task_returns_after_document_deleting_skip(monkeypatch):
    connection = FakeConnection()
    connection.cursor_obj.fetch_results = [{"id": 3}, {"id": 22, "status": "deleting"}]
    monkeypatch.setattr(indexing_worker, "get_connection", lambda: connection)
    monkeypatch.setattr(
        indexing_worker,
        "_extract_text_from_oss",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("不应读取或索引删除中的文档")),
    )

    indexing_worker._handle_index_task(41, 22, 3, {"object_key": "x", "filename": "x.txt"})

    assert any(
        '"skipped": "document_deleting"' in str(params)
        for _, params in connection.cursor_obj.queries
    )
    assert all("UPDATE document SET status = 'indexing'" not in sql for sql, _ in connection.cursor_obj.queries)
    assert connection.committed is True
    assert connection.rolled_back is False
