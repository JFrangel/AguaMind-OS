from collections.abc import AsyncGenerator

from agentos_llm import LLMFactory

from ..fusion import fuse_results
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
    system_prompt_override: str | None = None,
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
        "system_prompt_override": system_prompt_override,
    }

    if use_rag:
        tool = rag_tool or default_rag_tool()
        yield {"type": "status", "node": "rag", "content": status_text("rag.search", resolved)}
        rag_results = await tool.query(query, top_k=4)
        state["rag_context"] = rag_results
        if not rag_results:
            yield {
                "type": "status",
                "node": "rag",
                "content": status_text("rag.empty", resolved),
            }
        else:
            yield {
                "type": "status",
                "node": "rag",
                "content": status_text("rag.result", resolved, n=len(rag_results)),
            }
            yield {
                "type": "sources",
                "kind": "rag",
                "items": [
                    {
                        "id": h.get("id"),
                        "score": h.get("score"),
                        "filename": (h.get("metadata") or {}).get("filename"),
                        "snippet": (h.get("content") or "")[:200],
                    }
                    for h in rag_results
                ],
            }

    if use_web:
        tool = web_tool or default_web_tool()
        yield {"type": "status", "node": "web", "content": status_text("web.search", resolved)}
        web_results = await tool.search(query, top_k=3)
        state["web_context"] = web_results
        yield {
            "type": "status",
            "node": "web",
            "content": status_text("web.result", resolved, n=len(web_results)),
        }
        if web_results:
            yield {
                "type": "sources",
                "kind": "web",
                "items": [
                    {
                        "title": r.get("title"),
                        "url": r.get("url"),
                        "snippet": (r.get("snippet") or "")[:200],
                        "image": r.get("image"),
                    }
                    for r in web_results
                ],
            }

    # Re-rank when both modalities are active.
    if use_rag and use_web:
        state["fused_context"] = fuse_results(
            state.get("rag_context") or [],
            state.get("web_context") or [],
            top_k=6,
        )

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
