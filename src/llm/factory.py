from __future__ import annotations

from src.config import Settings
from src.llm.base import LLMProvider
from src.llm.cloud_provider import OpenAICompatibleProvider
from src.llm.local_provider import LocalOllamaProvider


def create_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider == "local":
        return LocalOllamaProvider(settings.local_base_url, settings.local_model)
    if settings.llm_provider == "cloud":
        return OpenAICompatibleProvider(
            settings.cloud_base_url,
            settings.cloud_model,
            settings.cloud_api_key,
        )
    raise ValueError(f"Unsupported provider: {settings.llm_provider}")
