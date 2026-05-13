from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class LLMMessage:
    role: str
    content: str


class LLMProvider(ABC):
    name: str

    @abstractmethod
    def generate(self, messages: list[LLMMessage]) -> str:
        """Generate text from a list of chat-style messages."""
