from __future__ import annotations

from pathlib import Path

import pytest

from src.prompts import load_system_prompt


def test_load_system_prompt(tmp_path: Path) -> None:
    prompt_file = tmp_path / "system_prompt.md"
    prompt_file.write_text("Use local processing.", encoding="utf-8")

    assert load_system_prompt(prompt_file) == "Use local processing."


def test_empty_prompt_is_rejected(tmp_path: Path) -> None:
    prompt_file = tmp_path / "system_prompt.md"
    prompt_file.write_text("   ", encoding="utf-8")

    with pytest.raises(ValueError):
        load_system_prompt(prompt_file)
