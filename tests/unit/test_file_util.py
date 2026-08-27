from util.file_util import chunk_text_by_sentence, clean_text_escapes, deduplicate_chunks


def test_clean_text_escapes_normalizes_whitespace():
    text = "  第一行\r\n\r\n\r\n第\t二   行  "

    assert clean_text_escapes(text) == "第一行\n\n第 二 行"


def test_deduplicate_chunks_keeps_first_original_value():
    chunks = ["第一段", "  第一段  ", "", "第二段"]

    assert deduplicate_chunks(chunks) == ["第一段", "第二段"]


def test_chunk_text_returns_empty_list_for_blank_content():
    assert chunk_text_by_sentence("   \n\n") == []


def test_long_sentence_chunks_respect_size_limit():
    chunks = chunk_text_by_sentence(
        "abcdefghijklmnopqrstuvwxy",
        max_chunk_size=10,
        overlap=2
    )

    assert len(chunks) == 4
    assert all(0 < len(chunk) <= 10 for chunk in chunks)
    assert chunks[1].startswith("ij")
