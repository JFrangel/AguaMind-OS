from agentos_llm import LLMFactory

from ..fusion import render_fused_block
from ..language import instruction, resolve
from ..state import AgentState

RESEARCHER_SYSTEM = """You are a research agent. Given a user query and (optionally)
already-gathered context from RAG and web sources, list 3-5 key facts, definitions, or
data points needed to answer it well. Be concise and grounded in the supplied context
when present.
Format: one finding per line, prefixed with "- ".
"""


async def researcher_node(state: AgentState, factory: LLMFactory) -> AgentState:
    query = state.get("query", "")
    language = resolve(state.get("language"), query)

    fused = state.get("fused_context") or []
    rag_context = state.get("rag_context") or []
    web_context = state.get("web_context") or []

    parts: list[str] = [f"Query: {query}"]

    # Prefer the re-ranked fused list when both modalities ran. Otherwise
    # fall back to the original two-block layout so single-modality runs
    # (only RAG, only Web) keep working unchanged.
    if fused:
        parts.append(render_fused_block(fused))
    else:
        if rag_context:
            parts.append("Internal context (RAG):")
            for item in rag_context:
                snippet = item.get("content", "")
                parts.append(f"- {snippet[:400]}")
        if web_context:
            parts.append("Web context:")
            for item in web_context:
                title = item.get("title", "")
                url = item.get("url", "")
                snippet = item.get("snippet", "")
                parts.append(f"- {title} ({url}): {snippet[:300]}")

    response = await factory.complete_with_fallback(
        messages=[
            {"role": "system", "content": f"{RESEARCHER_SYSTEM}\n\n{instruction(language)}"},
            {"role": "user", "content": "\n".join(parts)},
        ],
        cascade="speed",
        temperature=0.3,
        max_tokens=500,
    )
    findings = [
        line.lstrip("- ").strip()
        for line in response.content.splitlines()
        if line.strip().startswith("-")
    ]
    return {"findings": findings or [response.content.strip()]}
