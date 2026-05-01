import time

from .types import LLMProvider


class CircuitBreaker:
    def __init__(self, failure_threshold: int = 3, cooldown_seconds: int = 60):
        self._failure_threshold = failure_threshold
        self._cooldown_seconds = cooldown_seconds
        self._failures: dict[LLMProvider, int] = {}
        self._open_until: dict[LLMProvider, float] = {}

    def is_available(self, provider: LLMProvider) -> bool:
        if provider in self._open_until:
            if time.time() < self._open_until[provider]:
                return False
            del self._open_until[provider]
            self._failures[provider] = 0
        return True

    def record_failure(self, provider: LLMProvider) -> None:
        self._failures[provider] = self._failures.get(provider, 0) + 1
        if self._failures[provider] >= self._failure_threshold:
            self._open_until[provider] = time.time() + self._cooldown_seconds

    def record_success(self, provider: LLMProvider) -> None:
        self._failures[provider] = 0
        self._open_until.pop(provider, None)

    def get_status(self) -> dict[LLMProvider, dict]:
        return {
            provider: {
                "failures": self._failures.get(provider, 0),
                "available": self.is_available(provider),
            }
            for provider in LLMProvider
            if provider != LLMProvider.MOCK
        }
