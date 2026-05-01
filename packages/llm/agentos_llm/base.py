from abc import ABC, abstractmethod
from collections.abc import AsyncGenerator

from .types import LLMProvider, LLMResponse


class BaseLLMAdapter(ABC):
    provider: LLMProvider

    @abstractmethod
    async def complete(self, messages: list[dict], **kwargs) -> LLMResponse: ...

    @abstractmethod
    async def stream(self, messages: list[dict], **kwargs) -> AsyncGenerator[str, None]: ...

    @abstractmethod
    async def structured_output(self, messages: list[dict], schema: type, **kwargs) -> dict: ...

    @abstractmethod
    def is_available(self) -> bool: ...
