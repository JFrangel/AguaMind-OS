from collections.abc import AsyncGenerator

import pytest

from agentos_llm.base import BaseLLMAdapter
from agentos_llm.types import LLMProvider, LLMResponse


class FakeAdapter(BaseLLMAdapter):
    def __init__(
        self,
        provider: LLMProvider,
        *,
        available: bool = True,
        fail: bool = False,
        content: str = "ok",
    ):
        self.provider = provider
        self._available = available
        self._fail = fail
        self._content = content
        self.calls = 0

    def is_available(self) -> bool:
        return self._available

    async def complete(self, messages: list[dict], **kwargs) -> LLMResponse:
        self.calls += 1
        if self._fail:
            raise RuntimeError(f"{self.provider.value} simulated failure")
        return LLMResponse(content=self._content, provider=self.provider, model="fake")

    async def stream(self, messages: list[dict], **kwargs) -> AsyncGenerator[str, None]:
        if self._fail:
            raise RuntimeError(f"{self.provider.value} simulated failure")
        for token in self._content.split():
            yield token + " "

    async def structured_output(self, messages: list[dict], schema: type, **kwargs) -> dict:
        return {"ok": True}


@pytest.fixture
def fake_adapter():
    return FakeAdapter
