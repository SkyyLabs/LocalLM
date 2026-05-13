from __future__ import annotations

from pathlib import Path


def load_system_prompt(path: Path) -> str:
    if not path.exists():
        raise FileNotFoundError(f"System prompt file not found: {path}")
    prompt = path.read_text(encoding="utf-8").strip()
    if not prompt:
        raise ValueError(f"System prompt file is empty: {path}")
    return prompt
