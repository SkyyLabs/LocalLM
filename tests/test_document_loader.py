from __future__ import annotations

from pathlib import Path

import pytest

from src.document_loader import load_document


def test_load_text_document(tmp_path: Path) -> None:
    doc = tmp_path / "note.txt"
    doc.write_text("private note", encoding="utf-8")

    assert load_document(doc) == "private note"


def test_load_markdown_document(tmp_path: Path) -> None:
    doc = tmp_path / "note.md"
    doc.write_text("# Title", encoding="utf-8")

    assert load_document(doc) == "# Title"


def test_load_csv_document(tmp_path: Path) -> None:
    doc = tmp_path / "statement.csv"
    doc.write_text("date,amount\n2026-01-01,12.50\n", encoding="utf-8")

    assert "date, amount" in load_document(doc)
    assert "2026-01-01, 12.50" in load_document(doc)


def test_reject_unsupported_file(tmp_path: Path) -> None:
    doc = tmp_path / "image.png"
    doc.write_text("not supported", encoding="utf-8")

    with pytest.raises(ValueError):
        load_document(doc)
