from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Literal


ProviderName = Literal["local", "cloud"]


def _bool_env(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def load_dotenv(path: Path = Path(".env")) -> dict[str, str]:
    """Parse a simple .env file without requiring python-dotenv."""
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        values[key] = value
    return values


@dataclass(frozen=True)
class Settings:
    llm_provider: ProviderName = "local"
    local_base_url: str = "http://localhost:11434"
    local_model: str = "qwen2.5"
    cloud_base_url: str = "https://api.openai.com/v1"
    cloud_model: str = "gpt-4o-mini"
    cloud_api_key: str | None = None
    system_prompt_path: Path = Path("prompts/system_prompt.md")
    private_data_dir: Path = Path("data/private")
    allow_cloud_private_docs: bool = False

    @property
    def is_cloud(self) -> bool:
        return self.llm_provider == "cloud"


def load_settings(env_file: Path | None = Path(".env")) -> Settings:
    file_values: dict[str, str] = {}
    if env_file is not None:
        file_values = load_dotenv(env_file)

    def get_env(name: str, default: str | None = None) -> str | None:
        return os.getenv(name) or file_values.get(name) or default

    provider = (get_env("LLM_PROVIDER", "local") or "local").strip().lower()
    if provider not in {"local", "cloud"}:
        raise ValueError("LLM_PROVIDER must be either 'local' or 'cloud'.")

    return Settings(
        llm_provider=provider,  # type: ignore[arg-type]
        local_base_url=(get_env("LOCAL_LLM_BASE_URL", "http://localhost:11434") or "").rstrip("/"),
        local_model=get_env("LOCAL_LLM_MODEL", "qwen2.5") or "qwen2.5",
        cloud_base_url=(get_env("CLOUD_LLM_BASE_URL", "https://api.openai.com/v1") or "").rstrip("/"),
        cloud_model=get_env("CLOUD_LLM_MODEL", "gpt-4o-mini") or "gpt-4o-mini",
        cloud_api_key=get_env("CLOUD_LLM_API_KEY") or None,
        system_prompt_path=Path(get_env("SYSTEM_PROMPT_PATH", "prompts/system_prompt.md") or ""),
        private_data_dir=Path(get_env("PRIVATE_DATA_DIR", "data/private") or ""),
        allow_cloud_private_docs=_bool_env(get_env("ALLOW_CLOUD_PRIVATE_DOCS"), False),
    )
