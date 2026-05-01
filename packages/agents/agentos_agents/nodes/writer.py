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

When the answer is fundamentally numerical (rankings, time series,
comparisons, distributions), include a chart by emitting a fenced block
tagged `chart` with a JSON spec the UI will render as SVG:

```chart
{"type":"bar","title":"Ventas por mes","data":[["Ene",120],["Feb",95],["Mar",140]]}
```

Supported chart types: "bar" (categorical), "line" (sequential),
"area" (line with filled area). Data is an array of [label, value]
tuples. Optional fields: `title`, `subtitle`, `unit`. Use a chart only
when it adds value — don't chart 2 numbers, don't chart non-numeric data.

Avoid restating the query verbatim. Be specific.
"""

WRITER_SOURCES_DIRECTIVE = """When the user-provided context includes web sources, you MUST end your response
with a `## Fuentes` (or `## Sources` in English) section listing every source URL
as a markdown link. Format each entry as:
  - [Title](URL) — short note on what was used from this source

Do NOT skip this section when web context is provided. Inline-cite specific
facts where appropriate using `[name](URL)` so the reader can verify each
claim individually.
"""


def _format_web_block(web: list[dict]) -> str:
    """Render the web search context as a numbered block for the user message."""
    lines = ["Web sources (use these and cite their URLs in your answer):"]
    for i, item in enumerate(web, 1):
        title = item.get("title") or "(untitled)"
        url = item.get("url") or ""
        snippet = (item.get("snippet") or "").strip().replace("\n", " ")
        if len(snippet) > 280:
            snippet = snippet[:277] + "…"
        lines.append(f"[{i}] {title}\n    URL: {url}\n    {snippet}")
    return "\n".join(lines)


def _format_rag_block(rag: list[dict]) -> str:
    """Render the RAG hits as a citable block."""
    lines = ["Internal knowledge (RAG):"]
    for i, item in enumerate(rag, 1):
        meta = item.get("metadata") or {}
        source = meta.get("filename") or meta.get("source_id") or item.get("id") or "internal"
        snippet = (item.get("content") or "").strip().replace("\n", " ")
        if len(snippet) > 280:
            snippet = snippet[:277] + "…"
        lines.append(f"[INT-{i}] {source}\n    {snippet}")
    return "\n".join(lines)


async def writer_stream(state: AgentState, factory: LLMFactory) -> AsyncGenerator[str, None]:
    query = state.get("query", "")
    findings = state.get("findings", [])
    analysis = state.get("analysis", "")
    rag_context = state.get("rag_context") or []
    web_context = state.get("web_context") or []
    language = resolve(state.get("language"), query)

    parts = [f"Query: {query}"]
    if findings:
        parts.append("Findings:\n" + "\n".join(f"- {f}" for f in findings))
    if analysis:
        parts.append(f"Analysis:\n{analysis}")
    # Surface the raw web/RAG context AGAIN so the writer can quote URLs and
    # filenames directly. The researcher already condensed these into
    # findings, but the URLs get lost in summarisation — re-injecting them
    # here is the cheapest way to guarantee citation.
    if web_context:
        parts.append(_format_web_block(web_context))
    if rag_context:
        parts.append(_format_rag_block(rag_context))
    user_content = "\n\n".join(parts)

    # Only ask for the Sources section when there *are* sources to cite.
    # Without web/rag context the directive would force the writer to
    # invent links, which is worse than no citation.
    system = WRITER_SYSTEM
    if web_context:
        system = f"{system}\n\n{WRITER_SOURCES_DIRECTIVE}"

    cascade = state.get("cascade") or "speed"
    async for token in factory.stream_with_fallback(
        messages=[
            {"role": "system", "content": f"{system}\n\n{instruction(language)}"},
            {"role": "user", "content": user_content},
        ],
        cascade=cascade,
        temperature=0.7,
        max_tokens=1500,
    ):
        yield token


async def writer_node(state: AgentState, factory: LLMFactory) -> AgentState:
    chunks: list[str] = []
    async for token in writer_stream(state, factory):
        chunks.append(token)
    return {"response": "".join(chunks)}
