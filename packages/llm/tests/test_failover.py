import time

import pytest

from agentos_llm.failover import CircuitBreaker
from agentos_llm.types import LLMProvider


def test_starts_available():
    cb = CircuitBreaker()
    assert cb.is_available(LLMProvider.GROQ)


def test_opens_after_threshold():
    cb = CircuitBreaker(failure_threshold=3, cooldown_seconds=60)
    for _ in range(3):
        cb.record_failure(LLMProvider.GROQ)
    assert not cb.is_available(LLMProvider.GROQ)


def test_does_not_open_below_threshold():
    cb = CircuitBreaker(failure_threshold=3, cooldown_seconds=60)
    cb.record_failure(LLMProvider.GROQ)
    cb.record_failure(LLMProvider.GROQ)
    assert cb.is_available(LLMProvider.GROQ)


def test_success_resets_failures():
    cb = CircuitBreaker(failure_threshold=3, cooldown_seconds=60)
    cb.record_failure(LLMProvider.GROQ)
    cb.record_failure(LLMProvider.GROQ)
    cb.record_success(LLMProvider.GROQ)
    cb.record_failure(LLMProvider.GROQ)
    assert cb.is_available(LLMProvider.GROQ)


def test_recovers_after_cooldown(monkeypatch):
    cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=10)
    for _ in range(2):
        cb.record_failure(LLMProvider.GROQ)
    assert not cb.is_available(LLMProvider.GROQ)

    real_time = time.time
    monkeypatch.setattr(time, "time", lambda: real_time() + 11)
    assert cb.is_available(LLMProvider.GROQ)


def test_isolated_per_provider():
    cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=60)
    for _ in range(2):
        cb.record_failure(LLMProvider.GROQ)
    assert not cb.is_available(LLMProvider.GROQ)
    assert cb.is_available(LLMProvider.OPENROUTER)
