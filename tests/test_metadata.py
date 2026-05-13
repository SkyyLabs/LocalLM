from __future__ import annotations

from pathlib import Path

from src.metadata import load_metadata_file, merge_metadata, metadata_matches_filters, parse_key_value_pairs


def test_parse_key_value_pairs_coerces_values() -> None:
    metadata = parse_key_value_pairs(["year=2026", "reviewed=true", "kind=tax"])

    assert metadata == {"year": 2026, "reviewed": True, "kind": "tax"}


def test_load_metadata_file(tmp_path: Path) -> None:
    metadata_file = tmp_path / "metadata.json"
    metadata_file.write_text('{"doc.txt": {"kind": "note"}}', encoding="utf-8")

    assert load_metadata_file(metadata_file) == {"doc.txt": {"kind": "note"}}


def test_merge_metadata_adds_tags_and_source(tmp_path: Path) -> None:
    document = tmp_path / "doc.txt"
    metadata = merge_metadata(
        file_path=document,
        tags=["Tax Docs", "2026"],
        cli_metadata={"owner": "me"},
        metadata_by_file={"doc.txt": {"kind": "tax"}},
    )

    assert metadata["source"] == str(document)
    assert metadata["kind"] == "tax"
    assert metadata["owner"] == "me"
    assert metadata["tags"] == "2026,tax_docs"
    assert metadata["tag_tax_docs"] is True


def test_metadata_filter_matches_tag_booleans() -> None:
    assert metadata_matches_filters({"tag_tax": True}, {"tag_tax": True}) is True
    assert metadata_matches_filters({"tag_tax": False}, {"tag_tax": True}) is False
