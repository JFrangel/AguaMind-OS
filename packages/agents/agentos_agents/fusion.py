"""Re-ranking utilities to merge RAG and web results into a single context.

Without fusion, the agent sees two separate blocks (RAG hits + web hits) and
treats them as independent — useful for citation, bad for answering questions
that need both. This module normalises scores across modalities and produces
one ranked list the researcher can consume as a flat context.

Strategy is deliberately simple — no ML re-ranker model, no extra deps:

1. RAG hits already have a similarity score (0..1 cosine). Use it as-is.
2. Web hits don't have a score. Assign a positional score: the i-th result
   gets `web_base * (decay ** i)` where `web_base` defaults to 0.55 (slightly
   below average RAG hit so internal docs win ties) and `decay` = 0.85.
3. Merge into a single list, sort by score desc, cap at `top_k`.

The fused output keeps a `kind: "rag"|"web"` tag on each item so the writer
can still cite sources distinctly. This is fusion of *ranking*, not of
provenance.
"""
from __future__ import annotations

from typing import Any


def fuse_results(
    rag_hits: list[dict[str, Any]] | None,
    web_hits: list[dict[str, Any]] | None,
    *,
    top_k: int = 6,
    web_base: float = 0.55,
    web_decay: float = 0.85,
) -> list[dict[str, Any]]:
    """Merge RAG + Web hits into one re-ranked list.

    Each item in the output has shape:
        {"kind": "rag" | "web", "score": float, "content": str, "meta": {...}}

    `content` is the bit the LLM should read; `meta` carries the source-id
    (filename / url / title) so callers can render citations later.
    """
    fused: list[dict[str, Any]] = []

    for hit in rag_hits or []:
        score = hit.get("score")
        if not isinstance(score, (int, float)):
            score = 0.5
        meta = hit.get("metadata") or {}
        fused.append(
            {
                "kind": "rag",
                "score": float(score),
                "content": hit.get("content", ""),
                "meta": {
                    "id": hit.get("id"),
                    "filename": meta.get("filename"),
                    "source": meta.get("source"),
                },
            }
        )

    for i, hit in enumerate(web_hits or []):
        positional = web_base * (web_decay ** i)
        fused.append(
            {
                "kind": "web",
                "score": positional,
                "content": hit.get("snippet", ""),
                "meta": {
                    "title": hit.get("title"),
                    "url": hit.get("url"),
                },
            }
        )

    fused.sort(key=lambda x: x["score"], reverse=True)
    return fused[:top_k]


def render_fused_block(fused: list[dict[str, Any]]) -> str:
    """Format the fused list as a human-readable block to inject into the
    researcher's user message. Each entry is numbered and tagged so the
    writer can later cite [INT-1] vs [WEB-2] without knowing the ranking."""
    if not fused:
        return ""
    lines = ["Re-ranked context (RAG ⊕ Web, ordered by relevance):"]
    rag_n = 0
    web_n = 0
    for item in fused:
        if item["kind"] == "rag":
            rag_n += 1
            tag = f"INT-{rag_n}"
            src = item["meta"].get("filename") or item["meta"].get("id") or "internal"
        else:
            web_n += 1
            tag = f"WEB-{web_n}"
            src = item["meta"].get("title") or item["meta"].get("url") or "web"
        snippet = (item["content"] or "").strip().replace("\n", " ")
        if len(snippet) > 320:
            snippet = snippet[:317] + "…"
        lines.append(f"[{tag}] (score={item['score']:.2f}) {src} :: {snippet}")
    return "\n".join(lines)
