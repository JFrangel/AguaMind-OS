import asyncio
from collections.abc import AsyncGenerator

from agentos_llm import LLMFactory

from .analysis import AnalysisCrew
from .base import BaseCrew
from .writer import WriterCrew


_AGENT_LABELS = {
    "analysis": ["researcher", "analyst", "writer"],
    "writer": ["outliner", "writer"],
}


def _select_crew(name: str, factory: LLMFactory, cascade: str) -> tuple[BaseCrew, list[str]]:
    if name == "writer":
        return WriterCrew(factory, cascade=cascade), _AGENT_LABELS["writer"]
    return AnalysisCrew(factory, cascade=cascade), _AGENT_LABELS["analysis"]


async def run_crew_stream(
    task: str, context: dict, factory: LLMFactory
) -> AsyncGenerator[dict, None]:
    """Run a CrewAI crew, emitting status events for each agent and a final
    chunked token stream of the result.

    `context.crew` selects the crew: "analysis" (default) or "writer".
    CrewAI runs synchronously and returns the final output as a string. We
    surface progress through coarse-grained crew_status events and stream
    the final result to keep the UX consistent with the LangGraph path.
    """
    crew_name = context.get("crew", "analysis")
    crew, agents = _select_crew(crew_name, factory, context.get("cascade", "reasoning"))

    for agent in agents:
        yield {"type": "crew_status", "agent": agent, "task": f"{agent} starting"}

    inputs = {"query": task, "brief": task, **{k: v for k, v in context.items() if k in ("style",)}}
    loop = asyncio.get_running_loop()
    try:
        result = await loop.run_in_executor(None, crew.kickoff, inputs)
    except Exception as e:
        yield {"type": "error", "error": f"crew failed: {e}"}
        return

    for agent in agents:
        yield {"type": "crew_status", "agent": agent, "task": f"{agent} done"}

    for chunk in _chunk_text(result, size=80):
        yield {"type": "token", "content": chunk}
        await asyncio.sleep(0)

    yield {"type": "done"}


def _chunk_text(text: str, size: int = 80) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)] or [""]
