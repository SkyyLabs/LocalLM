from __future__ import annotations

from argparse import Namespace
from pathlib import Path

import pytest

import app
from src.config import Settings
from src.safety import UnsafeCloudProcessingError


def test_index_command_is_local_only(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(
        app,
        "load_settings",
        lambda: Settings(llm_provider="cloud", cloud_api_key="test-key", private_data_dir=tmp_path),
    )

    with pytest.raises(UnsafeCloudProcessingError):
        app.cmd_index(
            Namespace(
                path=tmp_path,
                metadata=None,
                metadata_file=None,
                tag=None,
                chunk_size=1200,
                overlap=150,
            )
        )
