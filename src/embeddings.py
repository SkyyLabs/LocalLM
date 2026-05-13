from __future__ import annotations

import requests


class LocalOllamaEmbeddingProvider:
    """Local embeddings through Ollama's /api/embeddings endpoint."""

    def __init__(self, base_url: str, model: str, timeout: int = 120) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def embed(self, text: str) -> list[float]:
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={"model": self.model, "prompt": text},
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise RuntimeError(
                "Could not generate local embeddings. Make sure Ollama is running and "
                f"the embedding model is pulled: ollama pull {self.model}"
            ) from exc

        data = response.json()
        embedding = data.get("embedding")
        if not isinstance(embedding, list) or not all(isinstance(value, (int, float)) for value in embedding):
            raise RuntimeError("Ollama returned an unexpected embedding response.")
        return [float(value) for value in embedding]

    def embed_many(self, texts: list[str]) -> list[list[float]]:
        return [self.embed(text) for text in texts]
