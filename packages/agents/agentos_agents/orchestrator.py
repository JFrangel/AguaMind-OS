from collections.abc import AsyncGenerator

from agentos_llm import LLMFactory

from .graphs import run_graph_stream, run_research_stream
from .tools import RAGTool, WebSearchTool


class Orchestrator:
    """Top-level entry point for agent execution.

    Decides between LangGraph (streaming chat with multi-agent reasoning) and
    CrewAI (structured collaborative tasks). Both emit SSE-style event dicts:
        {type: "status"|"token"|"crew_status"|"done"|"error", ...}

    Tools (RAG + Web) can be injected so the same orchestrator can hook into
    a process-wide RAG store or a per-tenant Tavily key without each call
    site rebuilding the wiring. When omitted, defaults are used (RAGPipeline
    singleton, DuckDuckGo HTML).
    """

    def __init__(
        self,
        llm_factory: LLMFactory | None = None,
        *,
        rag_tool: RAGTool | None = None,
        web_tool: WebSearchTool | None = None,
    ):
        self.llm_factory = llm_factory or LLMFactory()
        self.rag_tool = rag_tool
        self.web_tool = web_tool

    async def run(self, task: str, context: dict | None = None) -> AsyncGenerator[dict, None]:
        ctx = context or {}
        engine = ctx.get("engine") or self._pick_engine(ctx.get("type", "chat"))
        cascade = ctx.get("cascade", "speed")
        language = ctx.get("language")
        use_rag = bool(ctx.get("use_rag"))
        use_web = bool(ctx.get("use_web"))

        if engine == "crew":
            from .crews import run_crew_stream

            async for event in run_crew_stream(task, ctx, self.llm_factory):
                yield event
            return

        if engine == "research":
            async for event in run_research_stream(
                task,
                self.llm_factory,
                cascade=cascade,
                language=language,
                use_rag=use_rag,
                use_web=use_web,
                rag_tool=self.rag_tool,
                web_tool=self.web_tool,
            ):
                yield event
            return

        async for event in run_graph_stream(
            task,
            self.llm_factory,
            cascade=cascade,
            language=language,
            use_rag=use_rag,
            use_web=use_web,
            rag_tool=self.rag_tool,
            web_tool=self.web_tool,
        ):
            yield event

    @staticmethod
    def _pick_engine(task_type: str) -> str:
        # CrewAI shines for collaborative multi-step structured outputs.
        # research routes to a dedicated graph that always runs the full pipeline.
        if task_type in ("crew", "collaborate"):
            return "crew"
        if task_type == "research":
            return "research"
        return "graph"
