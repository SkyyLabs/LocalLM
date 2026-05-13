from __future__ import annotations

from src.chunking import chunk_text


def test_chunk_text_with_overlap() -> None:
    chunks = chunk_text("abcdefghij", chunk_size=5, overlap=2)

    assert chunks == ["abcde", "defgh", "ghij"]


def test_empty_text_returns_no_chunks() -> None:
    assert chunk_text("   ") == []
