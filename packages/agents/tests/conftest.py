from collections.abc import AsyncGenerator
from typing import Callable

import pytest

from agentos_llm.base import BaseLLMAdapter
from agentos_llm.factory import LLMFactory
from agentos_llm.failover import CircuitBreaker
from agentos_llm.types import LLMProvider, LLMResponse


class ScriptedAdapter(BaseLLMAdapter):
    """Returns content based on a router fn that inspects the messages.

    Used to simulate router classification + downstream node behavior in
    integration tests without hitting any real provider.
    """

    def __init__(self, route: Callable[[list[dict]], str], stream_text: str = "Hello world."):
        self.provider = LLMProvider.GROQ
        self._route = route
        self._stream_text = stream_text
        self.calls: list[list[dict]] = []

    def is_available(self) -> bool:
        return True

    async def complete(self, messages: list[dict], **kwargs) -> LLMResponse:
        self.calls.append(messages)
        return LLMResponse(content=self._route(messages), provider=self.provider, model="scripted")

    async def stream(self, messages: list[dict], **kwargs) -> AsyncGenerator[str, None]:
        self.calls.append(messages)
        for token in self._stream_text.split(" "):
            yield token + " "

    async def structured_output(self, messages: list[dict], schema: type, **kwargs) -> dict:
        return {"ok": True}


@pytest.fixture
def make_factory():
    def _build(adapter: BaseLLMAdapter) -> LLMFactory:
        f = LLMFactory.__new__(LLMFactory)
        f._adapters = {LLMProvider.GROQ: adapter}
        f.circuit_breaker = CircuitBreaker()
        return f

    return _build


@pytest.fixture
def scripted_adapter():
    return ScriptedAdapter
