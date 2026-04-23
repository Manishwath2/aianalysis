from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator

from app.schemas.chat import ChatCompletionMessage
from app.schemas.llm import LLMModel


class ProviderError(Exception):
    pass


class ProviderConfigError(ProviderError):
    pass


class ProviderRequestError(ProviderError):
    pass


class LLMProviderAdapter(ABC):
    provider_name: str

    @abstractmethod
    def is_configured(self) -> bool:
        raise NotImplementedError

    def default_model(self) -> str:
        return f"{self.provider_name}/default"

    @abstractmethod
    async def list_models(self) -> list[LLMModel]:
        raise NotImplementedError

    @abstractmethod
    async def complete_chat(self, *, messages: list[ChatCompletionMessage], model: str | None) -> str:
        raise NotImplementedError

    async def stream_chat(self, *, messages: list[ChatCompletionMessage], model: str | None) -> AsyncIterator[str]:
        text = await self.complete_chat(messages=messages, model=model)
        for token in text.split(" "):
            if token:
                yield token + " "
