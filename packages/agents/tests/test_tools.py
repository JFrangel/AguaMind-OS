"""RAG and Web search tools — verify the adapter contract using injected
callables so tests don't hit the network or require a vector store."""
import pytest

from agentos_agents.tools import RAGTool, WebSearchTool


@pytest.mark.asyncio
async def test_rag_tool_returns_query_results():
    async def fake_query(question: str, top_k: int):
        assert top_k == 4
        return [{"content": "doc-a", "score": 0.9}]

    tool = RAGTool(query_fn=fake_query)
    results = await tool.query("hello")
    assert results == [{"content": "doc-a", "score": 0.9}]


@pytest.mark.asyncio
async def test_rag_tool_swallows_errors():
    async def boom(question: str, top_k: int):
        raise RuntimeError("backend offline")

    tool = RAGTool(query_fn=boom)
    assert await tool.query("hi") == []


@pytest.mark.asyncio
async def test_web_tool_returns_search_results():
    async def fake_search(query: str, top_k: int):
        return [{"title": "wiki", "url": "https://example.com", "snippet": "..."}]

    tool = WebSearchTool(search_fn=fake_search)
    results = await tool.search("agents")
    assert results[0]["url"] == "https://example.com"


@pytest.mark.asyncio
async def test_web_tool_swallows_errors():
    async def boom(query: str, top_k: int):
        raise RuntimeError("rate limit")

    tool = WebSearchTool(search_fn=boom)
    assert await tool.search("anything") == []
