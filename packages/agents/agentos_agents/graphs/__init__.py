from .research import run_research_stream
from .runner import GraphEvent, run_graph_stream

__all__ = ["run_graph_stream", "run_research_stream", "GraphEvent", "build_chat_graph"]


def build_chat_graph(factory):
    """Lazy import: only require langgraph when the user actually wants the
    compiled DAG (for visualization or external integrations).
    """
    from .chat import build_chat_graph as _impl

    return _impl(factory)
