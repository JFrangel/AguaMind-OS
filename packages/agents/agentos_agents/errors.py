"""Friendly error messages for events emitted to the UI.

When all three LLM providers are rate-limited at the same time, the raw
exception is unreadable (multi-line JSON dumps, stack traces). The chat
panel needs something compact and actionable: short summary + per-provider
status + retry hint when available.

Used by the graph runner and the research stream when they catch
`AllProvidersFailedError`. Pure string parsing — no extra dependencies.
"""
from __future__ import annotations

import re

# Match `<LLMProvider.GROQ: 'groq'>` or `LLMProvider.GROQ` etc.
_PROVIDER_NAME = re.compile(r"LLMProvider\.([A-Z_]+)")
# Find a retry hint in seconds (e.g. "retry in 56.884s" or "retry in 27s")
_RETRY = re.compile(r"retry\s*(?:in)?\s*[:=]?\s*(\d+(?:\.\d+)?)\s*s", re.IGNORECASE)
# Try again in 4m13.152s style
_RETRY_MIN = re.compile(r"try\s+again\s+in\s+(\d+)m(\d+(?:\.\d+)?)s", re.IGNORECASE)
# Quota exceeded for metric…
_QUOTA = re.compile(r"quota\s+exceeded|RESOURCE_EXHAUSTED|rate[_\s-]?limit", re.IGNORECASE)


def _extract_retry_seconds(text: str) -> float | None:
    """Best-effort: return the smallest retry suggestion in seconds."""
    candidates: list[float] = []
    for match in _RETRY.finditer(text):
        try:
            candidates.append(float(match.group(1)))
        except ValueError:
            pass
    for match in _RETRY_MIN.finditer(text):
        try:
            mins = int(match.group(1))
            secs = float(match.group(2))
            candidates.append(mins * 60 + secs)
        except ValueError:
            pass
    return min(candidates) if candidates else None


def _classify(text: str) -> str:
    if _QUOTA.search(text):
        return "rate_limit"
    if "timeout" in text.lower() or "timed out" in text.lower():
        return "timeout"
    if "connection" in text.lower():
        return "connection"
    return "error"


_LANG_TEMPLATES = {
    "es": {
        "all_failed_rate": (
            "Los 3 proveedores de IA están sin cuota disponible ahora mismo. "
            "El sistema intentó {providers} y todos respondieron con rate limit."
        ),
        "all_failed_other": (
            "Los 3 proveedores de IA fallaron al responder. "
            "Probó {providers}."
        ),
        "retry_hint": "Volvé a intentar en ~{seconds}s.".replace("Volvé", "Vuelve"),
    },
    "en": {
        "all_failed_rate": (
            "All 3 LLM providers are out of quota right now. "
            "The system tried {providers} and each one returned rate limit."
        ),
        "all_failed_other": (
            "All 3 LLM providers failed. The system tried {providers}."
        ),
        "retry_hint": "Try again in ~{seconds}s.",
    },
}


def friendly_all_providers_failed(raw_error: str, language: str = "es") -> dict:
    """Convert a raw `AllProvidersFailedError` string into a structured event
    payload the UI can render without a wall of stack traces.

    Returns a dict with shape:
        {
            "type": "error",
            "kind": "all_providers_failed",
            "summary": "<one-line message>",
            "providers": [{"name": "groq", "reason": "rate_limit", "retry_seconds": 43.2}, …],
            "retry_seconds": <smallest hint, or None>,
            "raw": "<original text — kept for debugging>",
        }
    """
    text = str(raw_error)
    seen = list(dict.fromkeys(name.lower() for name in _PROVIDER_NAME.findall(text))) or [
        "groq",
        "openrouter",
        "gemini",
    ]

    # Per-provider classification by splitting around the parenthesised tuples
    # the cascade emits. Cheap heuristic: split on ", (<LLMProvider".
    chunks = re.split(r",\s*\(<LLMProvider", text)
    providers: list[dict] = []
    for i, name in enumerate(seen):
        chunk = chunks[i] if i < len(chunks) else text
        kind = _classify(chunk)
        retry = _extract_retry_seconds(chunk)
        providers.append({
            "name": name,
            "reason": kind,
            "retry_seconds": round(retry, 1) if retry is not None else None,
        })

    smallest_retry = min(
        (p["retry_seconds"] for p in providers if p["retry_seconds"] is not None),
        default=None,
    )

    template = _LANG_TEMPLATES.get(language, _LANG_TEMPLATES["es"])
    all_rate = all(p["reason"] == "rate_limit" for p in providers)
    summary_key = "all_failed_rate" if all_rate else "all_failed_other"
    summary = template[summary_key].format(providers=" · ".join(seen))
    if smallest_retry is not None:
        summary += " " + template["retry_hint"].format(seconds=int(smallest_retry))

    return {
        "type": "error",
        "kind": "all_providers_failed",
        "summary": summary,
        "providers": providers,
        "retry_seconds": smallest_retry,
        "raw": text[:1500],
    }
