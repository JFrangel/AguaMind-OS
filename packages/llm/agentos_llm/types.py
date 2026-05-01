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
