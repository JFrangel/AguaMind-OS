from collections.abc import AsyncGenerator

from agentos_llm import LLMFactory

from ..language import instruction, resolve
from ..state import AgentState

WRITER_SYSTEM = """You are the final responder. Write a clear, well-structured response
for the user using the prior research and analysis as input.

Format with Markdown when it helps the reader:
- short paragraphs for explanations
- bullet lists for enumerations
- tables (GitHub-style with `|`) when comparing things or summarising data
- fenced code blocks (```) for code, commands, or structured data
- inline code (`name`) for identifiers, file paths, or short terms

Avoid restating the query verbatim. Be specific. When you cite facts that came
from the supplied web/RAG context, surface the source as a link or short
attribution.
"""


async def writer_stream(state: AgentState, factory: LLMFactory) -> AsyncGenerator[str, None]:
    query = state.get("query", "")
    findings = state.get("findings", [])
    analysis = state.get("analysis", "")
    language = resolve(state.get("language"), query)

    parts = [f"Query: {query}"]
    if findings:
        parts.append("Findings:\n" + "\n".join(f"- {f}" for f in findings))
    if analysis:
        parts.append(f"Analysis:\n{analysis}")
    user_content = "\n\n".join(parts)

    adapter = factory.get(state.get("cascade") or "speed")
    async for token in adapter.stream(
        messages=[
            {"role": "system", "content": f"{WRITER_SYSTEM}\n\n{instruction(language)}"},
            {"role": "user", "content": user_content},
        ],
        temperature=0.7,
        max_tokens=1500,
    ):
        yield token


async def writer_node(state: AgentState, factory: LLMFactory) -> AgentState:
    chunks: list[str] = []
    async for token in writer_stream(state, factory):
        chunks.append(token)
    return {"response": "".join(chunks)}
