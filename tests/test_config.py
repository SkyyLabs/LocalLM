from __future__ import annotations

from pathlib import Path

from src.config import load_settings


def test_load_settings_defaults_to_local(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.delenv("LLM_PROVIDER", raising=False)

    settings = load_settings(env_file=tmp_path / "missing.env")

    assert settings.llm_provider == "local"
    assert settings.local_model == "qwen2.5"
    assert settings.allow_cloud_private_docs is False


def test_load_settings_from_env_file(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("LLM_PROVIDER", raising=False)
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "LLM_PROVIDER=cloud",
                "CLOUD_LLM_API_KEY=test-key",
                "ALLOW_CLOUD_PRIVATE_DOCS=true",
            ]
        ),
        encoding="utf-8",
    )

    settings = load_settings(env_file=env_file)

    assert settings.llm_provider == "cloud"
    assert settings.cloud_api_key == "test-key"
    assert settings.allow_cloud_private_docs is True
