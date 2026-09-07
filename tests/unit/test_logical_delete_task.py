import pytest

import crud.document_task_crud as document_task_crud
from crud.document_task_crud import DocumentTaskCRUD


class FakeCursor:
    def __init__(self, rows):
        self.rows = rows
        self.queries = []
        self.rowcount = 1
        self.lastrowid = 99

    def execute(self, sql, params=None):
        self.queries.append((sql, params))
        return 1

    def fetchall(self):
        return self.rows

    def close(self):
        pass


class FakeConnection:
    def __init__(self, rows):
        self.cursor_obj = FakeCursor(rows)
        self.committed = False

    def cursor(self, *args, **kwargs):
        return self.cursor_obj

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        self.committed = exc_type is None
        return False


@pytest.mark.parametrize(
    "task_type, document_id, expected_filter",
    [
        ("index", 22, "d.status NOT IN ('deleting', 'deleted')"),
        ("delete", 22, "d.status = 'deleting'"),
        ("delete_kb", 0, "dt.document_id = 0 AND kb.is_deleted = 1"),
    ],
)
def test_claim_next_filters_resource_state_and_records_owner(
        monkeypatch, task_type, document_id, expected_filter
):
    connection = FakeConnection([{
        "id": 11,
        "task_type": task_type,
        "document_id": document_id,
        "knowledge_base_id": 3,
        "status": "pending",
        "retry_count": 0,
        "max_retries": 5,
    }])
    monkeypatch.setattr(document_task_crud, "get_connection", lambda: connection)

    tasks = DocumentTaskCRUD.claim_next(task_type, "worker-a")

    assert len(tasks) == 1
    assert tasks[0].claimed_by == "worker-a"
    select_sql = connection.cursor_obj.queries[0][0]
    update_sql = connection.cursor_obj.queries[1][0]
    assert expected_filter in select_sql
    assert "FOR UPDATE SKIP LOCKED" in select_sql
    assert "claimed_by = %s" in update_sql
    assert "claimed_at = NOW()" in update_sql
    assert connection.committed is True


def test_document_task_rejects_zero_document_for_non_kb_delete():
    from model.document_task_model import DocumentTask

    with pytest.raises(ValueError):
        DocumentTask(task_type="delete", document_id=0, knowledge_base_id=3)
