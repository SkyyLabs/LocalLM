from __future__ import annotations

from pathlib import Path

from src.context_loader import load_context_documents, resolve_context_files


def test_resolve_context_files_supports_explicit_files_and_folder(tmp_path: Path) -> None:
    explicit = tmp_path / "explicit.txt"
    explicit.write_text("explicit", encoding="utf-8")
    folder = tmp_path / "folder"
    folder.mkdir()
    nested = folder / "nested.md"
    nested.write_text("nested", encoding="utf-8")
    ignored = folder / "ignored.png"
    ignored.write_text("ignored", encoding="utf-8")

    files = resolve_context_files([explicit], folder)

    assert files == [explicit, nested]


def test_load_context_documents_labels_sources(tmp_path: Path) -> None:
    first = tmp_path / "first.txt"
    second = tmp_path / "second.md"
    first.write_text("alpha", encoding="utf-8")
    second.write_text("beta", encoding="utf-8")

    document, files = load_context_documents([first, second], None)

    assert files == [first, second]
    assert document is not None
    assert f"--- Source: {first} ---" in document
    assert "alpha" in document
    assert f"--- Source: {second} ---" in document
    assert "beta" in document
