"""Cascade strategy picker shared by the writer and responder nodes.

Both nodes used to default to ``speed`` (Groq llama-3.3-70b first), which
is fast but produces shallow answers — listing facts without extracting
detail from rich context, refusing to engage with complex multi-part
questions. Now they call :func:`pick_cascade` which auto-upgrades to
``quality`` (OpenRouter heavy free models → Gemini → Groq) for any of:

  - The user provided web context with at least one fetched body.
  - The query is "complex" by heuristic — long, multi-sentence,
    comparison / list / analysis / code / step-by-step intent.

Simple chitchat ("hola", "cómo estás", "qué hora es") stays on
``speed`` so casual queries don't pay the latency cost.
"""
from __future__ import annotations

import re
from collections.abc import Iterable

# Words and phrases that signal "this needs depth, not a one-liner".
# Hits in ES + EN + a few PT/FR/DE/IT cognates so the heuristic survives
# multi-language usage.
# Each alternative is a *prefix* (e.g. `analiz` matches both "analiza"
# and "analizando"), so the regex starts with `\b` but does NOT end with
# one — adding a trailing boundary would block matches on Spanish/English
# inflections that don't end at a word break (e.g. "analiza", which has
# more letters after the prefix).
_COMPLEX_INTENT = re.compile(
    r"\b("
    # Comparison / contrast
    r"compar(?:a|ar|en|e|ing|aci[oó]n)|diferenci|contrast|"
    r"vs\b|versus|"
    # List / enumerate
    r"listam[ae]|listar|listado|enumera|enum[eé]r|menciona|"
    r"list\s|enumerate|"
    # Table / structured output
    r"tabla|comparativa|cuadr[oa]|matri[xz]|table|chart|breakdown|"
    # Analysis / explanation
    r"analiz|an[aá]lisis|examin|estudi|"
    r"explica|expl[íi]ca|describ|elabora|amplia|profundiz|d[ée]tall|"
    r"analy[sz]|examine|elaborate|in[- ]depth|deep[- ]dive|"
    # Code / implementation
    r"implement|escrib(?:e|ir|ime)|c[oó]digo|programa|funci[oó]n\s+que|"
    r"code\s|write\s+(?:a|the|some)|sample\s+code|"
    # Step-by-step / planning
    r"paso\s+a\s+paso|paso[- ]por[- ]paso|por\s+pasos|"
    r"step[- ]by[- ]step|step\s+\d|how\s+(?:do|to|can)\s+I|"
    # Deep architecture / design vocabulary
    r"arquitectur|workflow|pipeline|estrateg|design|trade[- ]?off|"
    # Multi-criteria / scoring
    r"pros\s+y\s+contras|ventajas\s+y\s+desventajas|recomienda|"
    r"pros\s+and\s+cons|recommend"
    r")",
    re.IGNORECASE,
)


def is_complex_query(query: str | None) -> bool:
    """True if the query looks like it needs a "thinking" model.

    Heuristic — three signals, any one fires:
      1. Length > 120 chars (a long question almost always needs depth).
      2. Multi-sentence (more than one period or question mark).
      3. Matches `_COMPLEX_INTENT` keyword set.
    """
    if not query:
        return False
    q = query.strip()
    if len(q) > 120:
        return True
    # Count terminal punctuation. ?? / ?! count as one each.
    sentences = sum(1 for ch in q if ch in ".?!¿¡")
    # Discount the trailing punctuation that's often just decorative.
    if q[-1:] in ".?!¿¡":
        sentences = max(0, sentences - 1)
    if sentences >= 1:  # at least one sentence-break inside the query
        return True
    if _COMPLEX_INTENT.search(q):
        return True
    return False


def has_rich_context(web_context: Iterable[dict] | None) -> bool:
    """True if at least one web source has a fetched article body.

    Empty-body items (timeouts, JS-only sites) don't count — without
    body the writer is stuck with the SERP snippet, which usually
    doesn't justify upgrading to a heavier model.
    """
    if not web_context:
        return False
    return any((item.get("body") or "").strip() for item in web_context)


def pick_cascade(
    query: str | None,
    web_context: Iterable[dict] | None = None,
    *,
    explicit: str | None = None,
) -> str:
    """Return the cascade name to use for this turn.

    Precedence:
      1. ``explicit`` (caller's override) wins always.
      2. ``quality`` if the web context has a fetched body.
      3. ``quality`` if the query itself looks complex.
      4. ``speed`` otherwise.
    """
    if explicit:
        return explicit
    if has_rich_context(web_context):
        return "quality"
    if is_complex_query(query):
        return "quality"
    return "speed"
