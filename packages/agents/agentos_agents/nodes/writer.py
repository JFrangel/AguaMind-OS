from collections.abc import AsyncGenerator

from agentos_llm import LLMFactory

from ..language import instruction, resolve
from ..state import AgentState

WRITER_SYSTEM = """You are the final responder of an AgentOS multi-agent
pipeline (router → researcher → analyst → writer). You have access to
all of AgentOS's capabilities and should answer accurately when asked
about them:

- LLM cascade with circuit breaker (Groq → OpenRouter → Gemini)
- RAG with SBERT (sentence-transformers MiniLM-L6-v2, 384-dim) + FAISS / pgvector
- Universal file adapter (PDF, DOCX, XLSX, CSV, JSON, MD, HTML, TXT, Parquet, XML, TSV)
- Web search (DuckDuckGo HTML scraping by default, Tavily when configured)
- NL → SQL with SafeQueryExecutor (Postgres / MySQL / SQLite, read-only)
- Notifications: Telegram + Email parallel via NotificationDispatcher
- Multi-language responses (es / en / pt / fr / de / it)
- PDF generation (ReportLab default, WeasyPrint when GTK is available)

If the user asks what AgentOS does, what stack is in use, what embeddings
you use, etc., answer with the facts above — don't pretend, don't
under-claim, don't recommend "you should add RAG" if it's already there.

EXECUTE the user's request directly.

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
  ✅ A ```chart``` fenced block with the actual data.

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

Anti-bloat rules — keep the response tight:
- Do NOT create sections, tables, columns, or rows you'd fill with
  placeholders like "No disponible", "N/A", "Not specified", "—", or
  "(no data)". If you don't have specific content for a topic, leave
  it out entirely. A blank cell or a "no data" cell wastes the user's
  time.
- Do NOT mirror words from source titles into your structure. If a
  source is titled "LangGraph vs CrewAI: costes, depuración, migración"
  but your findings don't actually contain numbers/details for those
  topics, do NOT build a "Costos reales" / "Depuración" / "Migración"
  section just because the title mentions them.
- Do NOT add `## Heading` blocks for content under ~3 substantive
  sentences. Headers are signposts for actual sub-sections, not
  decoration. A single-sentence "## Resumen" with one line under it is
  noise — fold it into the previous paragraph.
- One comparison table per response is usually enough. Don't follow it
  with "## Resumen de la comparativa" containing the same content
  reformatted.

Examples of bloat to avoid:
  ❌ "## Costos reales\n| Framework | Costos reales |\n| LangGraph | No disponible |\n| CrewAI | No disponible |"
  ✅ Just don't include the section.

  ❌ "## Resumen\nLa elección depende del proyecto."
  ✅ End the previous paragraph with that sentence inline.

Charts — STRICT rules. Only emit a ```chart``` fenced block when ALL of
these are true:
  1. You have at least 2 actual numerical data points with real numbers
     (sales figures, percentages, durations, counts, prices…).
  2. The numbers come from the user's query, the findings, or the
     analysis — NEVER invent numbers to fill a chart.
  3. The chart visually adds something a table or list can't show
     (trend over time, magnitude differences, distribution shape).

Do NOT emit a chart for:
  - Qualitative comparisons (framework A vs framework B, pros/cons,
    feature lists). Use a markdown table instead.
  - Definitions, explanations, summaries.
  - Anything where you'd need to fabricate numbers.

When you DO have real numerical data, the syntax is:

```chart
{"type":"bar","title":"Ventas por mes","data":[["Ene",120],["Feb",95],["Mar",140]]}
```

Chart types: "bar" (categorical), "line" (sequential), "area".
Data is an array of [label, value] tuples with NUMERIC values.
Optional fields: `title`, `subtitle`, `unit`.

Tone: confident, direct. Don't apologise for limitations unless you
genuinely can't do the task. Don't restate the query.
"""

WRITER_SOURCES_DIRECTIVE = """Citations — when web sources are in the context, attach them inline.

THE FORMAT IS A MARKDOWN LINK. The exact bytes are:
    space, open-bracket, number, close-bracket, open-paren, FULL URL, close-paren.

Example with real values:
    los agentes colaboran con roles definidos [1](https://www.truefoundry.com/es/blog/crewai-vs-langgraph).

The full URL inside the parentheses is REQUIRED. A bare digit, a digit
in brackets, or anything without the `(https://…)` part is broken.

  ❌ "los agentes colaboran con roles definidos 1."             (bare digit)
  ❌ "los agentes colaboran con roles definidos [1]."            (no URL)
  ❌ "los agentes colaboran [como se ve aquí](https://...)."     (link text is prose, not a number)
  ❌ "Según Crewai vs LangGraph: conozca las diferencias, los agentes…"
                                                                 (article title inlined as prose)
  ✅ "los agentes colaboran con roles definidos [1](https://www.truefoundry.com/es/blog/crewai-vs-langgraph)."

The number must match the `[N]` index in the `Web sources` block of the
user message. Don't renumber. Reuse the same number if the same source
backs multiple claims.

How many citations: aim for at least one per non-trivial paragraph and
one per row of a comparison table when sources are provided. If you
wrote 4 substantive factual claims, you should have ~4 markers.

Don't write a `## Fuentes` / `## Sources` / "Referencias" section. The
UI already lists every source as numbered pills under each message.
Duplicating that list in markdown is redundant.

Don't invent citations. If web context is missing, just write the answer
without any markers.
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
