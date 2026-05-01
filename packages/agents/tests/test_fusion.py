"""Tests for the RAG ⊕ Web re-ranker.

Verifies the score normalisation and ordering logic in
`agentos_agents.fusion`. No LLM calls — pure data transformation.
"""
from agentos_agents.fusion import fuse_results, render_fused_block


def test_fuse_orders_by_score_desc():
    rag = [
        {"id": "a", "content": "rag-low", "score": 0.30, "metadata": {"filename": "low.md"}},
        {"id": "b", "content": "rag-high", "score": 0.92, "metadata": {"filename": "high.md"}},
    ]
    web = [
        {"title": "wiki", "url": "https://x", "snippet": "web-1"},
    ]
    fused = fuse_results(rag, web, top_k=10)
    # rag-high (0.92) wins, web-1 (0.55) is second, rag-low (0.30) last
    assert [f["meta"].get("filename") or f["meta"].get("title") for f in fused] == [
        "high.md",
        "wiki",
        "low.md",
    ]


def test_fuse_caps_at_top_k():
    rag = [
        {"id": str(i), "content": f"r{i}", "score": 0.5, "metadata": {}}
        for i in range(10)
    ]
    fused = fuse_results(rag, [], top_k=3)
    assert len(fused) == 3


def test_fuse_handles_missing_score():
    """RAG hits without a numeric score should default to 0.5 instead of crashing."""
    rag = [{"id": "a", "content": "x", "metadata": {}}]
    fused = fuse_results(rag, [])
    assert len(fused) == 1
    assert fused[0]["score"] == 0.5


def test_fuse_web_decay_orders_correctly():
    """First web result should rank above the third even with same base score."""
    web = [
        {"title": "first", "url": "u1", "snippet": "..."},
        {"title": "second", "url": "u2", "snippet": "..."},
        {"title": "third", "url": "u3", "snippet": "..."},
    ]
    fused = fuse_results([], web, top_k=10)
    titles = [f["meta"]["title"] for f in fused]
    assert titles == ["first", "second", "third"]
    assert fused[0]["score"] > fused[1]["score"] > fused[2]["score"]


def test_render_fused_block_tags():
    fused = [
        {"kind": "rag", "score": 0.9, "content": "x", "meta": {"filename": "a.md"}},
        {"kind": "web", "score": 0.55, "content": "y", "meta": {"title": "wiki", "url": "u"}},
        {"kind": "rag", "score": 0.4, "content": "z", "meta": {"filename": "b.md"}},
    ]
    block = render_fused_block(fused)
    assert "[INT-1]" in block and "a.md" in block
    assert "[WEB-1]" in block and "wiki" in block
    assert "[INT-2]" in block and "b.md" in block


def test_render_empty_returns_empty_string():
    assert render_fused_block([]) == ""
