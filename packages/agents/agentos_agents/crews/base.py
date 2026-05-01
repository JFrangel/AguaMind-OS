import asyncio
from typing import Any

from agentos_llm import LLMFactory


class CrewLLM:
    """Sync LLM wrapper that CrewAI can call.

    CrewAI expects either a LiteLLM-compatible model string or an object with a
    `call(messages, **kwargs)` method. We provide the latter so all calls go
    through LLMFactory's cascade + circuit breaker.
    """

    def __init__(self, factory: LLMFactory, cascade: str = "reasoning"):
        self._factory = factory
        self._cascade = cascade
        self.model = "agentos-cascade"
        self.stop = None
        self.temperature = 0.7

    def call(self, messages: list[dict[str, Any]] | str, **kwargs: Any) -> str:
        if isinstance(messages, str):
            messages = [{"role": "user", "content": messages}]
        coro = self._factory.complete_with_fallback(
            messages=messages,
            cascade=kwargs.get("cascade", self._cascade),
            temperature=kwargs.get("temperature", self.temperature),
            max_tokens=kwargs.get("max_tokens", 2000),
        )
        return asyncio.run(coro).content

    def supports_function_calling(self) -> bool:
        return False

    def supports_stop_words(self) -> bool:
        return False

    def get_context_window_size(self) -> int:
        return 8192


class BaseCrew:
    """Base class for CrewAI crews wired into AgentOS LLM cascade."""

    def __init__(self, factory: LLMFactory, cascade: str = "reasoning"):
        self.factory = factory
        self.llm = CrewLLM(factory, cascade=cascade)

    def kickoff(self, inputs: dict[str, Any]) -> str:
        raise NotImplementedError
