from __future__ import annotations

from pathlib import Path

import pytest

from src.config import Settings
from src.safety import UnsafeCloudProcessingError, enforce_private_document_policy, is_private_path


def test_private_path_detection(tmp_path: Path) -> None:
    private_dir = tmp_path / "data" / "private"
    private_dir.mkdir(parents=True)
    private_file = private_dir / "tax.txt"
    private_file.write_text("secret", encoding="utf-8")

    assert is_private_path(private_file, private_dir) is True


def test_cloud_private_document_requires_confirmation(tmp_path: Path) -> None:
    private_dir = tmp_path / "data" / "private"
    private_dir.mkdir(parents=True)
    private_file = private_dir / "tax.txt"
    private_file.write_text("secret", encoding="utf-8")
    settings = Settings(llm_provider="cloud", cloud_api_key="test-key", private_data_dir=private_dir)

    with pytest.raises(UnsafeCloudProcessingError):
        enforce_private_document_policy(file_path=private_file, settings=settings)


def test_cloud_private_document_allows_explicit_confirmation(tmp_path: Path) -> None:
    private_dir = tmp_path / "data" / "private"
    private_dir.mkdir(parents=True)
    private_file = private_dir / "tax.txt"
    private_file.write_text("secret", encoding="utf-8")
    settings = Settings(llm_provider="cloud", cloud_api_key="test-key", private_data_dir=private_dir)

    enforce_private_document_policy(file_path=private_file, settings=settings, assume_yes=True)


def test_local_private_document_allowed(tmp_path: Path) -> None:
    private_dir = tmp_path / "data" / "private"
    private_dir.mkdir(parents=True)
    private_file = private_dir / "tax.txt"
    private_file.write_text("secret", encoding="utf-8")
    settings = Settings(llm_provider="local", private_data_dir=private_dir)

    enforce_private_document_policy(file_path=private_file, settings=settings)
