from __future__ import annotations

from pathlib import Path

from src.indexing import build_index_chunks, iter_supported_files


class FakeEmbedder:
    def embed(self, text: str) -> list[float]:
        return [float(len(text)), 1.0]


def test_iter_supported_files(tmp_path: Path) -> None:
    (tmp_path / "a.txt").write_text("a", encoding="utf-8")
    (tmp_path / "b.png").write_text("b", encoding="utf-8")

    assert iter_supported_files(tmp_path) == [tmp_path / "a.txt"]


def test_build_index_chunks(tmp_path: Path) -> None:
    document = tmp_path / "a.txt"
    document.write_text("abcdefghij", encoding="utf-8")

    chunks = build_index_chunks(
        path=tmp_path,
        embedder=FakeEmbedder(),  # type: ignore[arg-type]
        tags=["finance"],
        chunk_size=5,
        overlap=0,
    )

    assert len(chunks) == 2
    assert chunks[0].embedding == [5.0, 1.0]
    assert chunks[0].metadata["tag_finance"] is True
