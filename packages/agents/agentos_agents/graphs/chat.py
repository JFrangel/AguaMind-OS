from langgraph.graph import END, StateGraph

from agentos_llm import LLMFactory

from ..nodes import (
    analyst_node,
    researcher_node,
    responder_node,
    router_node,
    writer_node,
)
from ..state import AgentState


def _route_after_router(state: AgentState) -> str:
    intent = state.get("intent", "chat")
    if intent in ("research", "analysis", "writing"):
        return "researcher"
    return "responder"


def build_chat_graph(factory: LLMFactory):
    """Build the multi-agent chat graph.

    Flow:
        START → router
                ├── intent=chat       → responder → END
                └── intent=research/* → researcher → analyst → writer → END
    """
    graph = StateGraph(AgentState)

    graph.add_node("router", lambda s: router_node(s, factory))
    graph.add_node("researcher", lambda s: researcher_node(s, factory))
    graph.add_node("analyst", lambda s: analyst_node(s, factory))
    graph.add_node("writer", lambda s: writer_node(s, factory))
    graph.add_node("responder", lambda s: responder_node(s, factory))

    graph.set_entry_point("router")
    graph.add_conditional_edges(
        "router",
        _route_after_router,
        {"researcher": "researcher", "responder": "responder"},
    )
    graph.add_edge("researcher", "analyst")
    graph.add_edge("analyst", "writer")
    graph.add_edge("writer", END)
    graph.add_edge("responder", END)

    return graph.compile()
