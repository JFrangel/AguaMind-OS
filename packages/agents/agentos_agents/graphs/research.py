from collections.abc import AsyncGenerator

from agentos_llm import LLMFactory

from ..language import resolve, status_text
from ..nodes.analyst import analyst_node
from ..nodes.researcher import researcher_node
from ..nodes.writer import writer_stream
from ..state import AgentState
from ..tools import RAGTool, WebSearchTool, default_rag_tool, default_web_tool
from .runner import _error_event


async def run_research_stream(
    query: str,
    factory: LLMFactory,
    *,
    cascade: str = "reasoning",
    language: str | None = None,
    use_rag: bool = False,
    use_web: bool = False,
    rag_tool: RAGTool | None = None,
    web_tool: WebSearchTool | None = None,
) -> AsyncGenerator[dict, None]:
    """Dedicated research pipeline: skips the router and always runs
    researcher → analyst → writer with a reasoning-biased cascade.

    Used directly by /agents/research to give callers an explicit "give me
    the deep pipeline" entry point without relying on intent classification.
    """
    resolved = resolve(language, query)
    state: AgentState = {
        "query": query,
        "cascade": cascade,
        "language": resolved,
        "use_rag": use_rag,
        "use_web": use_web,
    }

    if use_rag:
        tool = rag_tool or default_rag_tool()
        yield {"type": "status", "node": "rag", "content": status_text("rag.search", resolved)}
        results = await tool.query(query, top_k=4)
        state["rag_context"] = results
        yield {
            "type": "status",
            "node": "rag",
            "content": status_text("rag.result", resolved, n=len(results)),
        }

    if use_web:
        tool = web_tool or default_web_tool()
        yield {"type": "status", "node": "web", "content": status_text("web.search", resolved)}
        results = await tool.search(query, top_k=3)
        state["web_context"] = results
        yield {
            "type": "status",
            "node": "web",
            "content": status_text("web.result", resolved, n=len(results)),
        }

    yield {
        "type": "status",
        "node": "researcher",
        "content": status_text("researcher.start", resolved),
    }
    try:
        state.update(await researcher_node(state, factory))
    except Exception as e:
        yield _error_event("researcher failed", e, resolved)
        return
    yield {
        "type": "status",
        "node": "researcher",
        "content": status_text(
            "researcher.result", resolved, n=len(state.get("findings", []))
        ),
    }

    yield {"type": "status", "node": "analyst", "content": status_text("analyst.start", resolved)}
    try:
        state.update(await analyst_node(state, factory))
    except Exception as e:
        yield _error_event("analyst failed", e, resolved)
        return
    yield {"type": "status", "node": "analyst", "content": status_text("analyst.result", resolved)}

    yield {"type": "status", "node": "writer", "content": status_text("writer.start", resolved)}
    try:
        async for token in writer_stream(state, factory):
            yield {"type": "token", "content": token}
    except Exception as e:
        yield _error_event("writer failed", e, resolved)
        return

    yield {"type": "done"}
