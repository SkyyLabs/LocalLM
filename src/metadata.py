from __future__ import annotations

import json
from pathlib import Path
from typing import Any


Metadata = dict[str, str | int | float | bool]


def parse_key_value_pairs(values: list[str] | None) -> Metadata:
    metadata: Metadata = {}
    for value in values or []:
        if "=" not in value:
            raise ValueError(f"Metadata must use key=value format: {value}")
        key, raw = value.split("=", 1)
        key = key.strip()
        if not key:
            raise ValueError("Metadata key cannot be empty.")
        metadata[key] = _coerce_value(raw.strip())
    return metadata


def load_metadata_file(path: Path | None) -> dict[str, Metadata]:
    if path is None:
        return {}
    if not path.exists():
        raise FileNotFoundError(f"Metadata file not found: {path}")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Metadata file must be a JSON object keyed by file path or file name.")

    result: dict[str, Metadata] = {}
    for key, value in data.items():
        if not isinstance(key, str) or not isinstance(value, dict):
            raise ValueError("Metadata file entries must map string paths to objects.")
        result[key] = {str(meta_key): _coerce_value(meta_value) for meta_key, meta_value in value.items()}
    return result


def merge_metadata(
    *,
    file_path: Path,
    tags: list[str] | None,
    cli_metadata: Metadata,
    metadata_by_file: dict[str, Metadata],
) -> Metadata:
    metadata: Metadata = {
        "source": str(file_path),
        "file_name": file_path.name,
        "extension": file_path.suffix.lower(),
    }

    file_metadata = (
        metadata_by_file.get(str(file_path))
        or metadata_by_file.get(str(file_path.resolve()))
        or metadata_by_file.get(file_path.name)
        or {}
    )
    metadata.update(file_metadata)
    metadata.update(cli_metadata)
    if tags:
        normalized_tags = sorted(set(_normalize_tag(tag) for tag in tags if tag.strip()))
        metadata["tags"] = ",".join(normalized_tags)
        for tag in normalized_tags:
            metadata[f"tag_{tag}"] = True
    return metadata


def metadata_matches_filters(metadata: dict[str, Any], filters: Metadata) -> bool:
    for key, expected in filters.items():
        actual = metadata.get(key)
        if key == "tags":
            actual_tags = {tag.strip() for tag in str(actual or "").split(",") if tag.strip()}
            expected_tags = {tag.strip() for tag in str(expected).split(",") if tag.strip()}
            if not expected_tags.issubset(actual_tags):
                return False
        elif str(actual) != str(expected):
            return False
    return True


def _coerce_value(value: Any) -> str | int | float | bool:
    if isinstance(value, bool | int | float):
        return value
    raw = str(value)
    lowered = raw.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        return int(raw)
    except ValueError:
        pass
    try:
        return float(raw)
    except ValueError:
        return raw


def _normalize_tag(tag: str) -> str:
    return "".join(character if character.isalnum() else "_" for character in tag.strip().lower()).strip("_")
