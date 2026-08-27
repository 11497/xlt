import json

from router.message_router import encode_stream_event


def test_encode_stream_event_produces_one_utf8_ndjson_line():
    encoded = encode_stream_event({"type": "delta", "content": "你好"})

    assert encoded.endswith("\n")
    assert encoded.count("\n") == 1
    assert "你好" in encoded
    assert json.loads(encoded) == {"type": "delta", "content": "你好"}
