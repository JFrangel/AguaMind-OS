from collections.abc import AsyncGenerator

from agentos_llm import LLMFactory

from ..language import instruction, resolve
from ..state import AgentState

RESPONDER_SYSTEM = (
    "You are a helpful, concise AI assistant. Answer directly. "
    "Use Markdown formatting when it helps the reader (lists, tables, "
    "fenced code blocks for code/commands, inline code for identifiers)."
)


async def responder_stream(state: AgentState, factory: LLMFactory) -> AsyncGenerator[str, None]:
    language = resolve(state.get("language"), state.get("query"))
    cascade = state.get("cascade") or "speed"
    # Profiles (`/apps/<slug>`) can replace the default system prompt without
    # touching the codebase. The language instruction is still appended so
    # the override author doesn't have to remember it.
    system = state.get("system_prompt_override") or RESPONDER_SYSTEM
    async for token in factory.stream_with_fallback(
        messages=[
            {"role": "system", "content": f"{system}\n\n{instruction(language)}"},
            {"role": "user", "content": state.get("query", "")},
        ],
        cascade=cascade,
        temperature=0.7,
    ):
        yield token


async def responder_node(state: AgentState, factory: LLMFactory) -> AgentState:
    chunks: list[str] = []
    async for token in responder_stream(state, factory):
        chunks.append(token)
    return {"response": "".join(chunks)}
