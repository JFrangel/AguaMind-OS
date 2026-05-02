from dataclasses import dataclass, field
from enum import Enum


class LLMProvider(str, Enum):
    GROQ = "groq"
    OPENROUTER = "openrouter"
    GEMINI = "gemini"
    MOCK = "mock"


@dataclass
class LLMResponse:
    content: str
    provider: LLMProvider
    model: str
    usage: dict = field(default_factory=dict)
    latency_ms: float = 0.0


class CascadeStrategy(str, Enum):
    SPEED = "speed"
    REASONING = "reasoning"
    CHEAP = "cheap"
    MULTIMODAL = "multimodal"
    # QUALITY: deeper, slower models for tasks that need to extract from
    # long/complex context. Prioritizes the strongest free models on
    # OpenRouter (DeepSeek V3, Qwen-72B, Hermes-405B) and Gemini Pro-class
    # before falling back to Groq. Use when context is rich (e.g. several
    # web articles with body text) and the response needs careful reading.
    QUALITY = "quality"
