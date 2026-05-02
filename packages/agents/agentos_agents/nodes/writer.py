from collections.abc import AsyncGenerator

from agentos_llm import LLMFactory

from ..language import instruction, resolve
from ..state import AgentState

WRITER_SYSTEM = """You are the final responder. EXECUTE the user's request directly.

CRITICAL: when the user asks to *create*, *make*, *generate*, *write*,
*build*, *list*, *compare*, etc., you MUST produce that artifact in the
response itself. NEVER tell the user how to create it, NEVER recommend
external tools (Canva, Excel, Notion, etc.), NEVER explain the concept
of what they're asking for unless they explicitly asked for an
explanation. Deliver the thing.

Examples of right vs wrong:
  ❌ "To create a comparison table, you can use tools like Canva, Visme…"
  ✅ A complete markdown table with all the rows the user asked for.

  ❌ "A timeline chart would help here. You could use Chart.js to…"
  ✅ A `\`\`\`chart` block with the actual data.

  ❌ "Here are some tips for writing a summary…"
  ✅ The actual summary.

Format with Markdown:
- Short paragraphs for explanations only when the user asked for one
- Bullet lists for enumerations
- Tables (GitHub-style with `|`) the moment the answer involves comparing,
  ranking, listing rows of data, or anything multi-attribute. Default to
  a table when in doubt.
- Fenced code blocks (```) for code, commands, configuration, structured data
- Inline code for identifiers, file paths, short terms

When the answer is fundamentally numerical (rankings, time series,
comparisons, distributions), include a chart by emitting a fenced block
tagged `chart`:

```chart
{"type":"bar","title":"Ventas por mes","data":[["Ene",120],["Feb",95],["Mar",140]]}
```

Chart types: "bar" (categorical), "line" (sequential), "area".
Data is an array of [label, value] tuples. Optional: `title`, `subtitle`, `unit`.
Use a chart only when it adds value — don't chart 2 numbers.

Tone: confident, direct. Don't apologise for limitations unless you
genuinely can't do the task. Don't restate the query.
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

    # Profile-level override: when /apps/<slug> sets a custom system
    # prompt (medical assistant, legal research, etc.) we replace the
    # generic WRITER_SYSTEM but still append the sources directive when
    # web context is present so citations stay consistent.
    base_system = state.get("system_prompt_override") or WRITER_SYSTEM
    system = base_system
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
