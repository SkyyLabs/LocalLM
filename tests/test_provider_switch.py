from __future__ import annotations

from src.config import Settings
from src.llm.cloud_provider import OpenAICompatibleProvider
from src.llm.factory import create_provider
from src.llm.local_provider import LocalOllamaProvider


def test_create_local_provider() -> None:
    provider = create_provider(Settings(llm_provider="local"))

    assert isinstance(provider, LocalOllamaProvider)


def test_create_cloud_provider() -> None:
    provider = create_provider(Settings(llm_provider="cloud", cloud_api_key="test-key"))

    assert isinstance(provider, OpenAICompatibleProvider)
