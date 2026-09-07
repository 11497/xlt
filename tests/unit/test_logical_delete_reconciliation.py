import pytest

import ai.reconciliation_service as reconciliation_service
from crud.document_crud import DocumentCRUD
from crud.document_task_crud import DocumentTaskCRUD
from model.document_model import Document
from model.document_task_model import DocumentTask


def make_doc(document_id=22, kb_id=3, status="ready", is_deleted=0):
    return Document.model_construct(
        id=document_id,
        knowledge_base_id=kb_id,
        filename="x.txt",
        storage_path="knowledge_base/3/x.txt",
        status=status,
        chunk_count=2,
        is_deleted=is_deleted,
    )


def test_failed_delete_tasks_are_not_requeued_as_index(monkeypatch):
    task = DocumentTask.model_construct(
        id=31,
        task_type="delete",
        document_id=22,
        knowledge_base_id=3,
        retry_count=1,
        max_retries=5,
    )
    monkeypatch.setattr(reconciliation_service.DocumentTaskCRUD, "get_failed_tasks", lambda **kwargs: [] if kwargs.get("task_type") == "index" else [task])

    executed = []

    class FakeCursor:
        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

        def execute(self, sql, params=None):
            executed.append(sql)

        def close(self):
            pass

    class FakeConnection:
        def cursor(self, *args, **kwargs):
            return FakeCursor()

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, traceback):
            return False

    monkeypatch.setattr(reconciliation_service, "get_connection", lambda: FakeConnection())
    assert reconciliation_service._recover_retryable_failed_tasks() == 0
    assert executed == []


def test_reconciliation_does_not_fix_deleting_document(monkeypatch):
    doc = make_doc(status="deleting")
    monkeypatch.setattr(DocumentCRUD, "get_by_status", lambda *_args, **_kwargs: [doc])

    created = []
    updated = []
    monkeypatch.setattr(reconciliation_service.DocumentTaskCRUD, "create", lambda task: created.append(task))
    monkeypatch.setattr(DocumentCRUD, "update_status", lambda *args, **kwargs: updated.append(args))

    fixed = reconciliation_service._check_and_fix_index_consistency()

    assert fixed == 0
    assert created == []
    assert updated == []
