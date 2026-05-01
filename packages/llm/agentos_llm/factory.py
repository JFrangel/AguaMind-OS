import time

from .base import BaseLLMAdapter
from .config import CASCADES, get_api_key, get_models
from .failover import CircuitBreaker
from .types import CascadeStrategy, LLMProvider, LLMResponse


class AllProvidersFailedError(Exception):
    pass


# Errors that justify trying the next model on the same provider before
# giving up and switching providers entirely. These are typically transient
# upstream conditions: rate-limits, quota exhaustion, capacity, single-model
# outages. Bad-key / 401 / 403 should NOT trigger model rotation — those
# affect every model on the provider, so jumping to the next provider is
# the right move.
_RETRYABLE_TOKENS = (
    "rate limit",
    "rate_limit",
    "ratelimit",
    "429",
    "quota",
    "resource_exhausted",
    "temporarily rate-limited",
    "overloaded",
    "capacity",
    "server_error",
    "503",
    "502",
)


def _is_model_retryable(exc: Exception) -> bool:
    """Should we try the next model on the same provider, or jump to the
    next provider? Heuristic on the exception's string representation."""
    text = str(exc).lower()
    return any(token in text for token in _RETRYABLE_TOKENS)


class LLMFactory:
    def __init__(self):
        self._adapters: dict[LLMProvider, BaseLLMAdapter] = {}
        self.circuit_breaker = CircuitBreaker()
        self._register_available()

    def _register_available(self) -> None:
        if get_api_key(LLMProvider.GROQ):
            from .adapters.groq import GroqAdapter

            self._adapters[LLMProvider.GROQ] = GroqAdapter()

        if get_api_key(LLMProvider.OPENROUTER):
            from .adapters.openrouter import OpenRouterAdapter

            self._adapters[LLMProvider.OPENROUTER] = OpenRouterAdapter()

        if get_api_key(LLMProvider.GEMINI):
            from .adapters.gemini import GeminiAdapter

            self._adapters[LLMProvider.GEMINI] = GeminiAdapter()

    def get(self, cascade: str | CascadeStrategy = CascadeStrategy.SPEED) -> BaseLLMAdapter:
        strategy = CascadeStrategy(cascade) if isinstance(cascade, str) else cascade
        for provider in CASCADES[strategy]:
            adapter = self._adapters.get(provider)
            if adapter and adapter.is_available() and self.circuit_breaker.is_available(provider):
                return adapter
        raise AllProvidersFailedError("No LLM providers available")

    async def complete_with_fallback(
        self, messages: list[dict], cascade: str | CascadeStrategy = CascadeStrategy.SPEED, **kwargs
    ) -> LLMResponse:
        """Run the cascade with two layers of fallback:

        Provider loop  → for each provider in the cascade, try its model list
            Model loop → walk PROVIDER_MODELS[provider] in order
                       │   - on success: return immediately
                       │   - on rate-limit / 429 / quota / 5xx: try next model
                       │   - on other errors (auth, bad request): mark
                       │     provider failed and break to next provider
                       └── on all models exhausted: mark failed, next provider

        Errors are accumulated per (provider, model, exception) so the UI
        can show exactly which combinations were tried. The caller-supplied
        `kwargs["model"]` (if any) overrides the entire model list — that
        path skips rotation since the caller asked for something specific.
        """
        strategy = CascadeStrategy(cascade) if isinstance(cascade, str) else cascade
        errors: list[tuple[LLMProvider, Exception]] = []
        forced_model = kwargs.get("model")

        for provider in CASCADES[strategy]:
            if not self.circuit_breaker.is_available(provider):
                continue
            adapter = self._adapters.get(provider)
            if not adapter or not adapter.is_available():
                continue

            models = [forced_model] if forced_model else get_models(provider)
            if not models:
                continue

            for model in models:
                try:
                    start = time.time()
                    call_kwargs = {**kwargs, "model": model}
                    result = await adapter.complete(messages, **call_kwargs)
                    result.latency_ms = (time.time() - start) * 1000
                    self.circuit_breaker.record_success(provider)
                    return result
                except Exception as e:
                    errors.append((provider, e))
                    if not _is_model_retryable(e):
                        # Not a transient model issue — treat as provider failure.
                        self.circuit_breaker.record_failure(provider)
                        break
                    # Transient: keep going down the provider's model list.
                    # Only escalate to the breaker once every model has been tried.
            else:
                # All models on this provider were retryable but failed.
                self.circuit_breaker.record_failure(provider)

        raise AllProvidersFailedError(f"All providers failed: {errors}")

    def get_status(self) -> dict:
        cb_status = self.circuit_breaker.get_status()
        providers = {}
        for provider in LLMProvider:
            if provider == LLMProvider.MOCK:
                continue
            adapter = self._adapters.get(provider)
            adapter_available = bool(adapter and adapter.is_available())
            cb_info = cb_status.get(provider, {})
            providers[provider.value] = {
                "registered": provider in self._adapters,
                "available": adapter_available and self.circuit_breaker.is_available(provider),
                "failures": cb_info.get("failures", 0),
            }
        return {"providers": providers}
