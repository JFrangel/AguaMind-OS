import os

from .types import CascadeStrategy, LLMProvider

CASCADES: dict[CascadeStrategy, list[LLMProvider]] = {
    CascadeStrategy.SPEED: [LLMProvider.GROQ, LLMProvider.OPENROUTER, LLMProvider.GEMINI],
    CascadeStrategy.REASONING: [LLMProvider.GEMINI, LLMProvider.OPENROUTER, LLMProvider.GROQ],
    CascadeStrategy.CHEAP: [LLMProvider.OPENROUTER, LLMProvider.GROQ, LLMProvider.GEMINI],
    CascadeStrategy.MULTIMODAL: [LLMProvider.GEMINI],
}

# Per-provider model lists. The factory walks each list in order: when a
# model returns a 429 / quota / rate-limit error, the next model in the
# same provider is tried before giving up and switching providers. Keeping
# this list long is the cheapest defence against the "all 3 providers
# rate-limited at the same time" problem when only the *primary* model is
# saturated upstream.
#
# Override the head of each list per environment with `MODEL_<PROVIDER>=<id>`.
PROVIDER_MODELS: dict[LLMProvider, list[str]] = {
    LLMProvider.GROQ: [
        "llama-3.3-70b-versatile",   # strongest free
        "llama-3.1-8b-instant",      # fastest free, separate token bucket
        "gemma2-9b-it",              # Google Gemma, separate bucket
        "mixtral-8x7b-32768",        # legacy but often available
    ],
    LLMProvider.OPENROUTER: [
        # The "OpenRouter Free" pool — meta-router across whatever free
        # models OpenRouter has available right now. When set, this
        # absorbs most rate-limit hits because OR moves you to a different
        # backend instead of failing.
        "openrouter/auto:free",
        # Specific community-hosted free models. Each one routes to a
        # different upstream provider, so when Venice is rate-limited
        # one of these usually still works.
        "meta-llama/llama-3.3-70b-instruct:free",
        "google/gemini-2.0-flash-exp:free",
        "qwen/qwen-2.5-72b-instruct:free",
        "deepseek/deepseek-chat:free",
        "mistralai/mistral-7b-instruct:free",
        "nousresearch/hermes-3-llama-3.1-405b:free",
        "microsoft/phi-3-medium-128k-instruct:free",
    ],
    LLMProvider.GEMINI: [
        "gemini-2.5-flash",          # 15 RPM free tier
        "gemini-2.5-flash-lite",     # smaller, separate quota
        "gemini-2.0-flash-exp",      # experimental tier
    ],
}

# Backward-compat: head of each list. Existing callers that import these
# constants keep working unchanged.
DEFAULT_MODELS: dict[LLMProvider, str] = {
    provider: models[0] for provider, models in PROVIDER_MODELS.items()
}
FREE_MODEL_ALTERNATIVES: dict[LLMProvider, list[str]] = PROVIDER_MODELS


def get_api_key(provider: LLMProvider) -> str | None:
    key_map = {
        LLMProvider.GROQ: "GROQ_API_KEY",
        LLMProvider.OPENROUTER: "OPENROUTER_API_KEY",
        LLMProvider.GEMINI: "GEMINI_API_KEY",
    }
    return os.getenv(key_map.get(provider, ""))


def get_model(provider: LLMProvider) -> str:
    """Read MODEL_<PROVIDER> env var if set, otherwise the head of the
    provider's model list. Lets ops swap models per environment without
    code changes."""
    env_key = f"MODEL_{provider.value.upper()}"
    return os.getenv(env_key) or DEFAULT_MODELS[provider]


def get_models(provider: LLMProvider) -> list[str]:
    """Full list of models the factory should walk for this provider.

    Order of resolution:
        1. `MODELS_<PROVIDER>` env var, comma-separated → use as-is.
        2. `MODEL_<PROVIDER>` env var → that single model first, then the
           rest of the built-in list (de-duplicated).
        3. The built-in `PROVIDER_MODELS` list.
    """
    plural_env = os.getenv(f"MODELS_{provider.value.upper()}")
    if plural_env:
        return [m.strip() for m in plural_env.split(",") if m.strip()]

    builtins = PROVIDER_MODELS.get(provider, [])
    override = os.getenv(f"MODEL_{provider.value.upper()}")
    if override:
        return [override] + [m for m in builtins if m != override]
    return list(builtins)
