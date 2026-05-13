from __future__ import annotations

import requests

from src.llm.base import LLMMessage, LLMProvider


class LocalOllamaProvider(LLMProvider):
    name = "local"

    def __init__(self, base_url: str, model: str, timeout: int = 120) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def generate(self, messages: list[LLMMessage]) -> str:
        payload = {
            "model": self.model,
            "messages": [message.__dict__ for message in messages],
            "stream": False,
        }

        try:
            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(
                "Could not reach Ollama. Make sure Ollama is running and the model is pulled."
            ) from exc

        data = response.json()
        content = data.get("message", {}).get("content")
        if not isinstance(content, str):
            raise RuntimeError("Ollama returned an unexpected response format.")
        return content
