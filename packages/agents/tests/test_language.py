"""Heuristic language detector + resolver — ensures Spanish is the default
and explicit state values trump auto-detection.
"""
from agentos_agents.language import DEFAULT_LANGUAGE, detect, instruction, resolve


def test_default_is_spanish():
    assert DEFAULT_LANGUAGE == "es"


def test_detects_spanish_keywords():
    assert detect("¿Cuál es la mejor base vectorial?") == "es"


def test_detects_english_keywords():
    assert detect("What is the best vector database?") == "en"


def test_detects_portuguese_keywords():
    assert detect("Qual é a melhor base vetorial? Olá") == "pt"


def test_returns_none_when_ambiguous():
    assert detect("xyz qwer") is None


def test_resolve_explicit_state_wins():
    assert resolve("fr", "Hello, what is this?") == "fr"


def test_resolve_falls_back_to_detection():
    assert resolve(None, "Comment ça va?") == "fr"


def test_resolve_falls_back_to_default():
    assert resolve(None, "xyz xyz") == "es"


def test_instruction_mentions_language_name():
    assert "Español" in instruction("es")
    assert "English" in instruction("en")
