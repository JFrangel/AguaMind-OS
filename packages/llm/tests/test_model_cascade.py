"""Tests for the per-provider model rotation in `complete_with_fallback`.

When a provider's primary model returns a 429 / rate-limit, the factory
should walk down the rest of that provider's model list before failing
over to the next provider. This is the difference between "Groq's
70b is saturated → try the 8b on the same key" and "Groq is dead → jump
to OpenRouter".
"""
from collections.abc import AsyncGenerator

import pytest

from agentos_llm.base import BaseLLMAdapter
from agentos_llm.factory import AllProvidersFailedError, LLMFactory
from agentos_llm.failover import CircuitBreaker
from agentos_llm.types import LLMProvider, LLMResponse


class ModelRotatingAdapter(BaseLLMAdapter):
    """Records every (model, attempt) and lets the test script per-call
    behaviour by populating `responses` with either an exception or a
    string response, keyed by model name."""

    def __init__(self, provider: LLMProvider, responses: dict[str, object]):
        self.provider = provider
        self._responses = responses
        self.calls: list[str] = []

    def is_available(self) -> bool:
        return True

    async def complete(self, messages: list[dict], **kwargs) -> LLMResponse:
        model = kwargs.get("model", "default")
        self.calls.append(model)
        outcome = self._responses.get(model)
        if isinstance(outcome, Exception):
            raise outcome
        return LLMResponse(content=str(outcome), provider=self.provider, model=model)

    async def stream(self, messages: list[dict], **kwargs) -> AsyncGenerator[str, None]:
        yield "ok"

    async def structured_output(self, messages: list[dict], schema: type, **kwargs) -> dict:
        return {}


def _factory(adapter: ModelRotatingAdapter) -> LLMFactory:
    f = LLMFactory.__new__(LLMFactory)
    f._adapters = {adapter.provider: adapter}
    f.circuit_breaker = CircuitBreaker(failure_threshold=99, cooldown_seconds=60)
    return f


@pytest.mark.asyncio
async def test_rotates_to_second_model_on_rate_limit(monkeypatch):
    """First model returns 429; second model on the SAME provider succeeds."""
    monkeypatch.setenv(
        "MODELS_GROQ", "llama-3.3-70b-versatile,llama-3.1-8b-instant,gemma2-9b-it"
    )

    adapter = ModelRotatingAdapter(
        LLMProvider.GROQ,
        responses={
            "llama-3.3-70b-versatile": RuntimeError(
                "Error code: 429 - Rate limit reached for tokens per day"
            ),
            "llama-3.1-8b-instant": "from-instant",
        },
    )
    factory = _factory(adapter)

    result = await factory.complete_with_fallback(
        [{"role": "user", "content": "hi"}], cascade="speed"
    )
    assert result.content == "from-instant"
    assert result.model == "llama-3.1-8b-instant"
    assert adapter.calls == [
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
    ]


@pytest.mark.asyncio
async def test_does_not_rotate_on_auth_error(monkeypatch):
    """Auth/4xx errors that aren't rate-limit shouldn't burn through every
    model on the provider — they affect the API key globally."""
    monkeypatch.setenv("MODELS_GROQ", "llama-3.3-70b-versatile,llama-3.1-8b-instant")

    adapter = ModelRotatingAdapter(
        LLMProvider.GROQ,
        responses={
            "llama-3.3-70b-versatile": RuntimeError(
                "401 Unauthorized: Invalid API key"
            ),
        },
    )
    factory = _factory(adapter)

    with pytest.raises(AllProvidersFailedError):
        await factory.complete_with_fallback(
            [{"role": "user", "content": "hi"}], cascade="speed"
        )

    # Only the first model was tried — auth doesn't rotate.
    assert adapter.calls == ["llama-3.3-70b-versatile"]


@pytest.mark.asyncio
async def test_exhausts_all_models_then_provider_fails(monkeypatch):
    """When every model on the provider returns 429, the cascade should
    finally give up on that provider and the factory raises."""
    monkeypatch.setenv("MODELS_GROQ", "a,b,c")

    err = RuntimeError("429 quota exceeded for free tier")
    adapter = ModelRotatingAdapter(
        LLMProvider.GROQ,
        responses={"a": err, "b": err, "c": err},
    )
    factory = _factory(adapter)

    with pytest.raises(AllProvidersFailedError) as exc:
        await factory.complete_with_fallback(
            [{"role": "user", "content": "hi"}], cascade="speed"
        )

    assert adapter.calls == ["a", "b", "c"]
    # All 3 attempts must be in the accumulated error list.
    assert str(exc.value).count("Provider.GROQ") >= 3 or str(exc.value).count("groq") >= 3


@pytest.mark.asyncio
async def test_forced_model_kwarg_skips_rotation(monkeypatch):
    """If the caller passes `model=...`, that exact model is tried — no
    rotation. This protects pinned model selection in production."""
    monkeypatch.setenv("MODELS_GROQ", "first,second,third")

    adapter = ModelRotatingAdapter(
        LLMProvider.GROQ,
        responses={"specific": "yes-specific"},
    )
    factory = _factory(adapter)

    result = await factory.complete_with_fallback(
        [{"role": "user", "content": "hi"}],
        cascade="speed",
        model="specific",
    )
    assert result.content == "yes-specific"
    assert adapter.calls == ["specific"]
