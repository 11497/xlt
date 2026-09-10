import hashlib
from unittest.mock import patch

import pymysql
import pytest

from crud.message_source_crud import (
    MessageSourceCRUD,
    SourceContentCRUD,
    build_message_sources,
    create_assistant_message_with_sources,
    sha256_hex,
)
from model.message_model import Message
from model.message_source_model import MessageSource
from model.schema_utils import SoftDeleteModel


class FakeCursor:
    def __init__(self, fetchone_results=None):
        self.queries = []
        self.fetchone_results = list(fetchone_results or [])
        self.executemany_calls = []
        self.lastrowid = 101
        self.rowcount = 1

    def execute(self, sql, params=None):
        self.queries.append((sql, params))
        return 1

    def executemany(self, sql, params_list):
        self.executemany_calls.append((sql, params_list))
        return len(params_list)

    def fetchone(self):
        if self.fetchone_results:
            return self.fetchone_results.pop(0)
        return None

    def close(self):
        pass


class FakeConnection:
    def __init__(self, cursor):
        self.cursor_obj = cursor
        self.committed = False
        self.rolled_back = False

    def cursor(self, *args, **kwargs):
        return self.cursor_obj

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, traceback):
        if exc is None:
            self.committed = True
        else:
            self.rolled_back = True
        return False


def _assistant_message():
    return Message(
        session_id=7,
        role="assistant",
        content="回答",
        create_time="2026-01-01T00:00:00"
    )


def test_source_content_hash_is_sha256():
    assert sha256_hex("内容") == hashlib.sha256("内容".encode("utf-8")).hexdigest()


def test_message_source_rejects_internal_soft_delete_fields():
    with pytest.raises(ValueError):
        MessageSource.model_validate({
            "message_id": 1,
            "session_id": 2,
            "source_content_id": 3,
            "knowledge_base_id": 4,
            "document_id": 5,
            "chunk_id": "5_0",
            "chunk_index": 0,
            "filename": "文档.md",
            "is_deleted": 1,
        })


def test_source_content_get_or_create_reuses_existing_hash():
    cursor = FakeCursor(fetchone_results=[{"id": 22}])

    assert SourceContentCRUD.get_or_create(cursor, "相同正文") == 22
    assert len(cursor.queries) == 1
    assert "content_hash" in cursor.queries[0][0]
    assert cursor.queries[0][1] == (hashlib.sha256("相同正文".encode()).hexdigest(),)


def test_source_content_get_or_create_handles_unique_conflict():
    cursor = FakeCursor(fetchone_results=[None, {"id": 33}])
    cursor.execute = lambda sql, params=None: (
        cursor.queries.append((sql, params)),
        (_ for _ in ()).throw(pymysql.err.IntegrityError(1062, "duplicate"))
        if sql.startswith("INSERT") else 1
    )[0]

    assert SourceContentCRUD.get_or_create(cursor, "并发正文") == 33
    assert [sql.split()[0] for sql, _ in cursor.queries] == ["SELECT", "INSERT", "SELECT"]


def test_build_message_sources_allows_same_content_with_different_chunks():
    chunks = [
        {
            "id": "1_0",
            "content": "相同正文",
            "metadata": {"document_id": 1, "knowledge_base_id": 2, "chunk_index": 0},
            "source": "vector",
            "rerank_score": 0.9,
        },
        {
            "id": "2_0",
            "content": "相同正文",
            "metadata": {"document_id": 2, "knowledge_base_id": 2, "chunk_index": 0},
            "source": "bm25",
            "rerank_score": 0.8,
        },
    ]

    with patch("crud.message_source_crud.get_filenames_by_document_ids", return_value={1: "一.md", 2: "二.md"}):
        sources = build_message_sources(7, chunks)

    assert [source.chunk_id for source in sources] == ["1_0", "2_0"]
    assert [source.filename for source in sources] == ["一.md", "二.md"]


def test_create_assistant_message_with_sources_uses_single_transaction(monkeypatch):
    cursor = FakeCursor(fetchone_results=[{"id": 44}])
    connection = FakeConnection(cursor)
    monkeypatch.setattr(
        "crud.message_source_crud.get_connection",
        lambda: connection,
    )

    sources = [
        MessageSource(
            message_id=None,
            session_id=None,
            source_content_id=None,
            knowledge_base_id=2,
            document_id=3,
            chunk_id="3_0",
            chunk_index=0,
            filename="文档.md",
        )
    ]

    message_id = create_assistant_message_with_sources(_assistant_message(), sources)

    assert message_id == 101
    assert sources[0].message_id == 101
    assert sources[0].session_id == 7
    assert sources[0].source_content_id == 44
    assert sources[0].sort_order == 0
    insert_params = cursor.executemany_calls[0][1][0]
    assert insert_params[2] == 44
    assert len(cursor.executemany_calls) == 1
    assert connection.committed is True
    assert connection.rolled_back is False


def test_delete_by_session_soft_deletes_sources_before_messages(monkeypatch):
    cursor = FakeCursor()
    connection = FakeConnection(cursor)
    monkeypatch.setattr(
        "crud.message_crud.get_connection",
        lambda: connection,
    )

    from crud.message_crud import MessageCRUD

    assert MessageCRUD.delete_by_session_id(7) is True
    assert [sql.split()[1] for sql, _ in cursor.queries] == ["message_source", "message"]
    assert connection.committed is True


def test_delete_message_with_after_soft_deletes_sources_before_messages(monkeypatch):
    cursor = FakeCursor()
    connection = FakeConnection(cursor)
    monkeypatch.setattr(
        "crud.message_crud.get_connection",
        lambda: connection,
    )

    from crud.message_crud import MessageCRUD

    assert MessageCRUD.delete_message_with_after(7, 9) is True
    assert [sql.split()[1] for sql, _ in cursor.queries] == ["message_source", "message"]
    assert connection.committed is True

def test_get_sources_grouped_by_message_ids_avoids_n_plus_one(monkeypatch):
    class Cursor:
        def __init__(self):
            self.queries = []

        def execute(self, sql, params=None):
            self.queries.append((sql, params))
            return 1

        def fetchall(self):
            return [
                {
                    "message_id": 11,
                    "chunk_id": "1_0",
                    "chunk_index": 0,
                    "document_id": 1,
                    "filename": "a.md",
                    "knowledge_base_id": 2,
                    "rerank_score": 0.9,
                    "recall_source": "vector",
                    "sort_order": 0,
                    "content": "??A",
                },
                {
                    "message_id": 12,
                    "chunk_id": "2_0",
                    "chunk_index": 0,
                    "document_id": 2,
                    "filename": "b.md",
                    "knowledge_base_id": 2,
                    "rerank_score": 0.8,
                    "recall_source": "bm25",
                    "sort_order": 0,
                    "content": "??B",
                },
            ]

        def close(self):
            pass

    class CursorContext:
        def __init__(self, cursor):
            self.cursor = cursor

        def __enter__(self):
            return self.cursor

        def __exit__(self, exc_type, exc, traceback):
            return False

    cursor = Cursor()
    monkeypatch.setattr(
        "crud.message_source_crud.get_cursor",
        lambda: CursorContext(cursor),
    )

    from crud.message_source_crud import get_sources_grouped_by_message_ids

    grouped = get_sources_grouped_by_message_ids([11, 12])

    assert list(grouped.keys()) == [11, 12]
    assert grouped[11][0]["chunk_id"] == "1_0"
    assert grouped[12][0]["chunk_id"] == "2_0"
    assert "message_id" not in grouped[11][0]
    assert len(cursor.queries) == 1

