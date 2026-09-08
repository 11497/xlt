import asyncio
import inspect
from contextlib import contextmanager
from pathlib import Path

import pytest

from scripts import restore_deleted_document as restore


class FakeCursor:
    def __init__(self, results=(), *, update_rowcount=1, fail_on=None):
        self.results = list(results)
        self.queries = []
        self.rowcount = 1
        self.update_rowcount = update_rowcount
        self.fail_on = fail_on

    def execute(self, sql, params=None):
        self.queries.append((sql, params))
        if self.fail_on and self.fail_on in sql:
            raise RuntimeError("模拟数据库失败")
        self.rowcount = self.update_rowcount if "UPDATE document SET" in sql else 1

    def fetchone(self):
        return self.results.pop(0) if self.results else None

    def close(self):
        pass


class FakeConnection:
    def __init__(self, cursor, *, commit_error=False):
        self.cursor_obj = cursor
        self.commit_error = commit_error
        self.committed = False
        self.rolled_back = False

    def cursor(self, *_args, **_kwargs):
        return self.cursor_obj

    def commit(self):
        if self.commit_error:
            raise RuntimeError("模拟提交失败")
        self.committed = True

    def rollback(self):
        self.rolled_back = True


@contextmanager
def connection_context(connection):
    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise


class FakeIngestion:
    def __init__(self, status="success", *, chroma_ok=True, es_ok=True, ingest_error=None):
        self.status = status
        self.chroma_ok = chroma_ok
        self.es_ok = es_ok
        self.ingest_error = ingest_error
        self.delete_calls = []
        self.ingest_calls = []

    def delete_document(self, knowledge_base_id, document_id):
        self.delete_calls.append((knowledge_base_id, document_id))
        return {"chroma": self.chroma_ok, "es": self.es_ok}

    def ingest_document(self, knowledge_base_id, document_id, chunks):
        self.ingest_calls.append((knowledge_base_id, document_id, chunks))
        if self.ingest_error:
            raise self.ingest_error
        return {
            "status": self.status,
            "chroma_ok": self.status in ("success", "partial"),
            "es_ok": self.status == "success",
            "chunk_count": len(chunks),
        }


def target():
    return restore.RestoreTarget(
        22,
        3,
        "课程资料.txt",
        "knowledge_base/3/" + "a" * 32 + "_课程资料.txt",
        "deleted",
        2,
    )


def document_row(**overrides):
    row = {
        "id": 22,
        "knowledge_base_id": 3,
        "filename": "课程资料.txt",
        "storage_path": "knowledge_base/3/" + "a" * 32 + "_课程资料.txt",
        "status": "deleted",
        "chunk_count": 2,
        "is_deleted": 1,
    }
    row.update(overrides)
    return row


def patch_connection(monkeypatch, results, **connection_kwargs):
    cursor_kwargs = {
        key: value
        for key, value in connection_kwargs.items()
        if key in {"update_rowcount", "fail_on"}
    }
    cursor = FakeCursor(results, **cursor_kwargs)
    connection = FakeConnection(cursor, commit_error=connection_kwargs.get("commit_error", False))
    monkeypatch.setattr(restore, "get_connection", lambda: connection_context(connection))
    return connection, cursor


def test_load_target_rejects_missing_document(monkeypatch):
    patch_connection(monkeypatch, [None])
    with pytest.raises(restore.RestoreBlockedError, match="不存在"):
        restore.load_restore_target(22)


def test_load_target_rejects_document_not_deleted(monkeypatch):
    patch_connection(monkeypatch, [document_row(is_deleted=0, status="ready")])
    with pytest.raises(restore.RestoreBlockedError, match="不是已删除状态"):
        restore.load_restore_target(22)


@pytest.mark.parametrize("knowledge_base", [None, {"id": 3, "is_deleted": 1}])
def test_load_target_rejects_missing_or_deleted_knowledge_base(monkeypatch, knowledge_base):
    patch_connection(monkeypatch, [document_row(), knowledge_base])
    with pytest.raises(restore.RestoreBlockedError):
        restore.load_restore_target(22)


def test_load_target_rejects_missing_oss_location(monkeypatch):
    patch_connection(monkeypatch, [document_row(storage_path="")])
    with pytest.raises(restore.RestoreBlockedError, match="OSS"):
        restore.load_restore_target(22)


@pytest.mark.parametrize("status", ["pending", "processing"])
def test_preflight_rejects_active_document_task(monkeypatch, status):
    task = {"id": 9, "task_type": "delete", "status": status}
    connection, _ = patch_connection(monkeypatch, [document_row(), {"id": 3, "is_deleted": 0}, task])
    with pytest.raises(restore.RestoreBlockedError, match="文档存在活动任务"):
        restore.load_restore_target(22)
    assert connection.rolled_back is True


def test_preflight_rejects_active_knowledge_base_delete_task(monkeypatch):
    task = {"id": 10, "task_type": "delete_kb", "status": "processing"}
    patch_connection(monkeypatch, [document_row(), {"id": 3, "is_deleted": 0}, None, task])
    with pytest.raises(restore.RestoreBlockedError, match="知识库存在活动删除任务"):
        restore.load_restore_target(22)


def test_preflight_failure_does_not_start_external_work(monkeypatch):
    task = {"id": 9, "task_type": "index", "status": "pending"}
    patch_connection(monkeypatch, [document_row(), {"id": 3, "is_deleted": 0}, task])
    monkeypatch.setattr(restore, "DOCUMENT_ID", 22)
    monkeypatch.setattr(restore, "parse_args", lambda: type("Args", (), {"execute": True})())
    monkeypatch.setattr(
        restore,
        "execute_restore",
        lambda _target: (_ for _ in ()).throw(AssertionError("不得访问外部服务")),
    )
    assert restore.main() == 2


def test_restore_uploaded_filename_only_removes_exact_upload_prefix():
    object_key = "knowledge_base/3/0123456789abcdef0123456789abcdef_课程资料.pdf"
    assert restore.restore_uploaded_filename(object_key, "课程资料.pdf") == "课程资料.pdf"
    assert restore.restore_uploaded_filename(object_key, "另一个.pdf") == "另一个.pdf"
    assert restore.restore_uploaded_filename(
        "knowledge_base/3/normal_课程资料.pdf", "normal_课程资料.pdf"
    ) == "normal_课程资料.pdf"
    assert restore._safe_temp_filename("..\\课程资料.pdf") == "课程资料.pdf"


@pytest.mark.parametrize("status", ["partial", "failed"])
def test_ingestion_failure_compensates_both_indexes(status):
    ingestion = FakeIngestion(status=status)
    assert restore.restore_indexes(target(), ["一"], ingestion) is False
    assert ingestion.ingest_calls == [(3, 22, ["一"])]
    assert ingestion.delete_calls == [(3, 22), (3, 22)]


def test_ingestion_exception_compensates_both_indexes():
    ingestion = FakeIngestion(ingest_error=RuntimeError("embedding down"))
    assert restore.restore_indexes(target(), ["一"], ingestion) is False
    assert ingestion.delete_calls == [(3, 22), (3, 22)]


def test_success_delegates_to_ingestion_without_building_es_payload():
    ingestion = FakeIngestion(status="success")
    chunks = ["一", "二"]
    assert restore.restore_indexes(target(), chunks, ingestion) is True
    assert ingestion.ingest_calls == [(3, 22, chunks)]
    source = inspect.getsource(restore.restore_indexes)
    assert "add_documents" not in source
    assert "chunk_id" not in source


def test_empty_document_skips_ingestion_write():
    ingestion = FakeIngestion(status="success")
    assert restore.restore_indexes(target(), [], ingestion) is True
    assert ingestion.ingest_calls == []
    assert ingestion.delete_calls == [(3, 22)]


def test_empty_document_restores_ready_with_zero_chunk_count(monkeypatch):
    connection, cursor = patch_connection(monkeypatch, [{"id": 3}, {"id": 22}, None, None])
    ingestion = FakeIngestion(status="success")
    monkeypatch.setattr(restore, "IngestionService", lambda: ingestion)
    monkeypatch.setattr(restore, "parse_chunks", _parse_chunks_with_temp_file([]))

    assert restore.execute_restore(target()) is True
    assert ingestion.ingest_calls == []
    update = next(item for item in cursor.queries if "UPDATE document SET" in item[0])
    assert update[1] == (0, 22, 3)
    assert connection.committed is True


def test_cleanup_failure_stops_before_ingestion_write():
    ingestion = FakeIngestion(status="success", es_ok=False)
    assert restore.restore_indexes(target(), ["一"], ingestion) is False
    assert ingestion.ingest_calls == []
    assert ingestion.delete_calls == [(3, 22)]


def test_dry_run_does_not_trigger_external_work(monkeypatch, capsys):
    monkeypatch.setattr(restore, "DOCUMENT_ID", 22)
    monkeypatch.setattr(restore, "load_restore_target", lambda _id: target())
    monkeypatch.setattr(
        restore,
        "execute_restore",
        lambda _target: (_ for _ in ()).throw(AssertionError("dry-run 不应执行")),
    )
    monkeypatch.setattr(restore, "parse_args", lambda: type("Args", (), {"execute": False})())
    assert restore.main() == 0
    output = capsys.readouterr().out
    assert "活动任务检查：通过" in output
    assert "dry-run" in output


def test_download_to_tempfile_only_reads_oss(monkeypatch, tmp_path):
    calls = []

    class FakeOSS:
        async def __aenter__(self):
            return self

        async def __aexit__(self, *_args):
            pass

        async def get_file(self, object_key):
            calls.append(object_key)
            return {"exists": True, "content": b"test content"}

        async def delete_file(self, *_args):
            raise AssertionError("恢复脚本不得删除 OSS 对象")

    monkeypatch.setattr(restore, "OSSUtil", FakeOSS)
    local_path = asyncio.run(restore.download_to_tempfile(target(), Path(tmp_path)))
    assert local_path.read_bytes() == b"test content"
    assert calls == [target().storage_path]


def test_mark_document_ready_restores_database_state(monkeypatch):
    connection, cursor = patch_connection(monkeypatch, [{"id": 3}, {"id": 22}, None, None])
    assert restore.mark_document_ready(target(), 4) is True
    update = next(item for item in cursor.queries if "UPDATE document SET" in item[0])
    assert update[1] == (4, 22, 3)
    assert "is_deleted = 0" in update[0] and "status = 'ready'" in update[0]
    assert connection.committed is True


def _parse_chunks_with_temp_file(chunks, *, error=None, captured=None):
    async def fake_parse(_target, directory):
        if captured is not None:
            captured.append(directory)
        (directory / "download.tmp").write_text("temporary", encoding="utf-8")
        if error:
            raise error
        return chunks

    return fake_parse


@pytest.mark.parametrize(
    "results",
    [
        [{"id": 3}, {"id": 22}, {"id": 9, "task_type": "index", "status": "pending"}],
        [{"id": 3}, {"id": 22}, None, {"id": 10, "task_type": "delete_kb", "status": "processing"}],
    ],
)
def test_final_active_task_rolls_back_and_compensates(monkeypatch, results):
    connection, _ = patch_connection(monkeypatch, results)
    ingestion = FakeIngestion(status="success")
    monkeypatch.setattr(restore, "IngestionService", lambda: ingestion)
    monkeypatch.setattr(restore, "parse_chunks", _parse_chunks_with_temp_file([]))

    assert restore.execute_restore(target()) is False
    assert connection.rolled_back is True
    assert ingestion.delete_calls == [(3, 22), (3, 22)]


@pytest.mark.parametrize("failure", ["update_rowcount", "commit_error"])
def test_database_write_failure_rolls_back_and_compensates(monkeypatch, failure):
    kwargs = {"update_rowcount": 0} if failure == "update_rowcount" else {"commit_error": True}
    connection, _ = patch_connection(monkeypatch, [{"id": 3}, {"id": 22}, None, None], **kwargs)
    ingestion = FakeIngestion(status="success")
    monkeypatch.setattr(restore, "IngestionService", lambda: ingestion)
    monkeypatch.setattr(restore, "parse_chunks", _parse_chunks_with_temp_file(["一"]))

    assert restore.execute_restore(target()) is False
    assert connection.rolled_back is True
    assert ingestion.delete_calls == [(3, 22), (3, 22)]


def test_successful_execute_updates_database_and_cleans_temp_directory(monkeypatch):
    captured = []
    connection, cursor = patch_connection(monkeypatch, [{"id": 3}, {"id": 22}, None, None])
    ingestion = FakeIngestion(status="success")
    monkeypatch.setattr(restore, "IngestionService", lambda: ingestion)
    monkeypatch.setattr(
        restore,
        "parse_chunks",
        _parse_chunks_with_temp_file(["一", "二"], captured=captured),
    )

    assert restore.execute_restore(target()) is True
    assert ingestion.ingest_calls == [(3, 22, ["一", "二"])]
    update = next(item for item in cursor.queries if "UPDATE document SET" in item[0])
    assert update[1] == (2, 22, 3)
    assert connection.committed is True
    assert captured and not captured[0].exists()


def test_parse_failure_cleans_temp_directory_without_constructing_ingestion(monkeypatch):
    captured = []
    monkeypatch.setattr(
        restore,
        "parse_chunks",
        _parse_chunks_with_temp_file([], error=RuntimeError("parse failed"), captured=captured),
    )
    monkeypatch.setattr(
        restore,
        "IngestionService",
        lambda: (_ for _ in ()).throw(AssertionError("解析失败时不应创建索引服务")),
    )

    with pytest.raises(RuntimeError, match="parse failed"):
        restore.execute_restore(target())
    assert captured and not captured[0].exists()
