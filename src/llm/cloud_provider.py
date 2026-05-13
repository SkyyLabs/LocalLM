from __future__ import annotations

import requests

from src.llm.base import LLMMessage, LLMProvider


class OpenAICompatibleProvider(LLMProvider):
    name = "cloud"

    def __init__(
        self,
        base_url: str,
        model: str,
        api_key: str | None,
        timeout: int = 120,
    ) -> None:
        if not api_key:
            raise ValueError("CLOUD_LLM_API_KEY is required when LLM_PROVIDER=cloud.")
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.api_key = api_key
        self.timeout = timeout

    def generate(self, messages: list[LLMMessage]) -> str:
        payload = {
            "model": self.model,
            "messages": [message.__dict__ for message in messages],
        }
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        try:
            response = requests.post(
                f"{self.base_url}/chat/completions",
                json=payload,
                headers=headers,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError("Cloud LLM request failed.") from exc

        data = response.json()
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError("Cloud provider returned an unexpected response format.") from exc
        if not isinstance(content, str):
            raise RuntimeError("Cloud provider returned non-text content.")
        return content
