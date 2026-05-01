from collections.abc import AsyncGenerator
from dataclasses import dataclass

from agentos_llm import LLMFactory

from ..errors import friendly_all_providers_failed
from ..language import resolve, status_text
from ..nodes.analyst import analyst_node
from ..nodes.researcher import researcher_node
from ..nodes.responder import responder_stream
from ..nodes.router import router_node
from ..nodes.writer import writer_stream
from ..state import AgentState
from ..tools import RAGTool, WebSearchTool, default_rag_tool, default_web_tool

GraphEvent = dict


# Map a runner node label to the i18n status key for its "starting" message.
_NODE_START_KEY = {
    "router": "router.classify",
    "researcher": "researcher.start",
    "analyst": "analyst.start",
    "writer": "writer.start",
    "responder": "responder.start",
    "rag": "rag.search",
    "web": "web.search",
}


def _emit_status(node: str, language: str, content: str | None = None) -> GraphEvent:
    if content is not None:
        return {"type": "status", "node": node, "content": content}
    key = _NODE_START_KEY.get(node)
    text = status_text(key, language) if key else node
    return {"type": "status", "node": node, "content": text}


def _error_event(prefix: str, exc: Exception, language: str | None) -> dict:
    """Convert a node failure into a UI-friendly error event. When the cause
    is `AllProvidersFailedError` we expand it into a structured payload with
    per-provider status + retry hint; everything else falls back to a compact
    one-line message.
    """
    from agentos_llm.factory import AllProvidersFailedError

    if isinstance(exc, AllProvidersFailedError):
        ev = friendly_all_providers_failed(str(exc), language or "es")
        ev["error"] = ev["summary"]  # legacy field expected by older UIs
        ev["stage"] = prefix
        return ev
    return {"type": "error", "error": f"{prefix}: {exc}", "stage": prefix}


async def run_graph_stream(
    query: str,
    factory: LLMFactory,
    cascade: str = "speed",
    *,
    language: str | None = None,
    use_rag: bool = False,
    use_web: bool = False,
    rag_tool: RAGTool | None = None,
    web_tool: WebSearchTool | None = None,
) -> AsyncGenerator[GraphEvent, None]:
    """Run the multi-agent chat graph, yielding SSE events as nodes execute.

    Token streaming happens during the final node (writer or responder) so the
    user sees real-time output. Earlier nodes emit only status events.

    `use_rag` / `use_web` toggle external context gathering before the
    researcher runs. They are independent: enabling both gives the agent
    internal docs *and* fresh web results.
    """
    resolved_language = resolve(language, query)
    state: AgentState = {
        "query": query,
        "cascade": cascade,
        "language": resolved_language,
        "use_rag": use_rag,
        "use_web": use_web,
    }

    lang = resolved_language
    yield _emit_status("router", lang)
    try:
        update = await router_node(state, factory)
        state.update(update)
        yield {
            "type": "status",
            "node": "router",
            "content": status_text(
                "router.intent", lang, intent=state.get("intent", "chat"), language=lang
            ),
        }
    except Exception as e:
        yield _error_event("router failed", e, lang)
        return

    intent = state.get("intent", "chat")

    if intent in ("research", "analysis", "writing"):
        try:
            if use_rag:
                tool = rag_tool or default_rag_tool()
                yield _emit_status("rag", lang)
                rag_results = await tool.query(query, top_k=4)
                state["rag_context"] = rag_results
                yield {
                    "type": "status",
                    "node": "rag",
                    "content": status_text("rag.result", lang, n=len(rag_results)),
                }

            if use_web:
                tool = web_tool or default_web_tool()
                yield _emit_status("web", lang)
                web_results = await tool.search(query, top_k=3)
                state["web_context"] = web_results
                yield {
                    "type": "status",
                    "node": "web",
                    "content": status_text("web.result", lang, n=len(web_results)),
                }

            yield _emit_status("researcher", lang)
            update = await researcher_node(state, factory)
            state.update(update)
            yield {
                "type": "status",
                "node": "researcher",
                "content": status_text(
                    "researcher.result", lang, n=len(state.get("findings", []))
                ),
            }

            yield _emit_status("analyst", lang)
            update = await analyst_node(state, factory)
            state.update(update)
            yield {
                "type": "status",
                "node": "analyst",
                "content": status_text("analyst.result", lang),
            }

            yield _emit_status("writer", lang)
            async for token in writer_stream(state, factory):
                yield {"type": "token", "content": token}
        except Exception as e:
            yield _error_event("pipeline failed", e, lang)
            return
    else:
        try:
            yield _emit_status("responder", lang)
            async for token in responder_stream(state, factory):
                yield {"type": "token", "content": token}
        except Exception as e:
            yield _error_event("responder failed", e, lang)
            return

    yield {"type": "done"}


@dataclass
class CompiledGraph:
    """Thin wrapper exposing the LangGraph compiled object alongside the runner.

    Kept so consumers can `compiled.graph.get_graph()` for visualization
    while still using the streaming runner for chat.
    """
    graph: object
