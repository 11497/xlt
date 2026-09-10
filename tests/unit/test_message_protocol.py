import json

from router.message_router import encode_stream_event


def test_encode_stream_event_produces_one_utf8_ndjson_line():
    encoded = encode_stream_event({"type": "delta", "content": "你好"})

    assert encoded.endswith("\n")
    assert encoded.count("\n") == 1
    assert "你好" in encoded
    assert json.loads(encoded) == {"type": "delta", "content": "你好"}


def test_encode_stream_event_allows_done_sources():
    encoded = encode_stream_event({
        "type": "done",
        "assistant_message_id": 12,
        "sources": [{
            "chunk_id": "1_0",
            "content": "校园规定",
        }]
    })

    assert encoded.endswith("\n")
    assert encoded.count("\n") == 1
    assert "校园规定" in encoded
    assert json.loads(encoded)["type"] == "done"
    assert json.loads(encoded)["sources"][0]["chunk_id"] == "1_0"


def test_encode_stream_event_allows_stopped_sources():
    encoded = encode_stream_event({
        "type": "stopped",
        "assistant_message_id": 12,
        "sources": [{
            "chunk_id": "1_0",
            "content": "校园规定",
        }]
    })

    assert encoded.endswith("\n")
    assert json.loads(encoded)["type"] == "stopped"
    assert json.loads(encoded)["sources"][0]["chunk_id"] == "1_0"
