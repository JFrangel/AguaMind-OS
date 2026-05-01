import pytest

from agentos_llm.factory import AllProvidersFailedError, LLMFactory
from agentos_llm.types import CascadeStrategy, LLMProvider


@pytest.fixture
def factory_with(fake_adapter):
    """Build a factory with a custom set of fake adapters bypassing env keys."""

    def _build(adapters: dict[LLMProvider, object]) -> LLMFactory:
        f = LLMFactory.__new__(LLMFactory)
        from agentos_llm.failover import CircuitBreaker

        f._adapters = adapters
        f.circuit_breaker = CircuitBreaker(failure_threshold=2, cooldown_seconds=60)
        return f

    return _build


@pytest.mark.asyncio
async def test_picks_first_available(factory_with, fake_adapter):
    adapters = {
        LLMProvider.GROQ: fake_adapter(LLMProvider.GROQ, content="from-groq"),
        LLMProvider.OPENROUTER: fake_adapter(LLMProvider.OPENROUTER, content="from-or"),
        LLMProvider.GEMINI: fake_adapter(LLMProvider.GEMINI, content="from-gemini"),
    }
    factory = factory_with(adapters)

    result = await factory.complete_with_fallback([{"role": "user", "content": "hi"}], cascade="speed")
    assert result.provider == LLMProvider.GROQ
    assert result.content == "from-groq"


@pytest.mark.asyncio
async def test_falls_through_on_failure(factory_with, fake_adapter):
    adapters = {
        LLMProvider.GROQ: fake_adapter(LLMProvider.GROQ, fail=True),
        LLMProvider.OPENROUTER: fake_adapter(LLMProvider.OPENROUTER, content="from-or"),
        LLMProvider.GEMINI: fake_adapter(LLMProvider.GEMINI, content="from-gemini"),
    }
    factory = factory_with(adapters)

    result = await factory.complete_with_fallback([{"role": "user", "content": "hi"}], cascade="speed")
    assert result.provider == LLMProvider.OPENROUTER
    assert adapters[LLMProvider.GROQ].calls == 1


@pytest.mark.asyncio
async def test_skips_unavailable_provider(factory_with, fake_adapter):
    adapters = {
        LLMProvider.GROQ: fake_adapter(LLMProvider.GROQ, available=False),
        LLMProvider.OPENROUTER: fake_adapter(LLMProvider.OPENROUTER, content="from-or"),
    }
    factory = factory_with(adapters)

    result = await factory.complete_with_fallback([{"role": "user", "content": "hi"}], cascade="speed")
    assert result.provider == LLMProvider.OPENROUTER
    assert adapters[LLMProvider.GROQ].calls == 0


@pytest.mark.asyncio
async def test_all_fail_raises(factory_with, fake_adapter):
    adapters = {
        LLMProvider.GROQ: fake_adapter(LLMProvider.GROQ, fail=True),
        LLMProvider.OPENROUTER: fake_adapter(LLMProvider.OPENROUTER, fail=True),
        LLMProvider.GEMINI: fake_adapter(LLMProvider.GEMINI, fail=True),
    }
    factory = factory_with(adapters)

    with pytest.raises(AllProvidersFailedError):
        await factory.complete_with_fallback([{"role": "user", "content": "hi"}], cascade="speed")


@pytest.mark.asyncio
async def test_circuit_opens_after_repeated_failures(factory_with, fake_adapter):
    adapters = {
        LLMProvider.GROQ: fake_adapter(LLMProvider.GROQ, fail=True),
        LLMProvider.OPENROUTER: fake_adapter(LLMProvider.OPENROUTER, content="ok"),
    }
    factory = factory_with(adapters)

    # First call: groq fails (1), or succeeds
    await factory.complete_with_fallback([{"role": "user", "content": "1"}], cascade="speed")
    # Second call: groq fails (2 → opens), or succeeds
    await factory.complete_with_fallback([{"role": "user", "content": "2"}], cascade="speed")

    # Third call: circuit open, groq must be skipped without being called
    groq_calls_before = adapters[LLMProvider.GROQ].calls
    await factory.complete_with_fallback([{"role": "user", "content": "3"}], cascade="speed")
    assert adapters[LLMProvider.GROQ].calls == groq_calls_before


@pytest.mark.asyncio
async def test_cascade_reasoning_prefers_gemini(factory_with, fake_adapter):
    adapters = {
        LLMProvider.GROQ: fake_adapter(LLMProvider.GROQ, content="groq"),
        LLMProvider.OPENROUTER: fake_adapter(LLMProvider.OPENROUTER, content="or"),
        LLMProvider.GEMINI: fake_adapter(LLMProvider.GEMINI, content="gemini"),
    }
    factory = factory_with(adapters)

    result = await factory.complete_with_fallback(
        [{"role": "user", "content": "hi"}], cascade=CascadeStrategy.REASONING
    )
    assert result.provider == LLMProvider.GEMINI


def test_get_status_shape(factory_with, fake_adapter):
    adapters = {
        LLMProvider.GROQ: fake_adapter(LLMProvider.GROQ),
        LLMProvider.OPENROUTER: fake_adapter(LLMProvider.OPENROUTER, available=False),
    }
    factory = factory_with(adapters)
    status = factory.get_status()

    assert "providers" in status
    assert status["providers"]["groq"]["registered"] is True
    assert status["providers"]["groq"]["available"] is True
    assert status["providers"]["openrouter"]["available"] is False
    assert status["providers"]["gemini"]["registered"] is False
