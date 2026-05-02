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

WRITER_SOURCES_DIRECTIVE = """When the user-provided context includes web sources, you MUST cite them
inline. The UI already renders a numbered pill list of all web sources at
the bottom of every assistant message — your job is to point each claim
at the source that backs it.

REQUIRED:
- At least one inline `[N](URL)` marker per non-trivial paragraph (and
  per table column when comparing) whenever web sources are provided.
  If you wrote 4 distinct factual claims, expect ~4 inline markers.
- Use the exact `[N]` number that appears in the `Web sources` block
  the user message gives you. Don't renumber. Reuse the same N if the
  same source backs multiple claims.

DO NOT:
- Do NOT write a `## Fuentes` / `## Sources` / "Referencias" section at
  the end. The frontend already shows the source list as numbered pills
  underneath every message — duplicating it as markdown is redundant
  noise.
- Do NOT inline the article title as prose ("Según [título]…", "Como
  se menciona en [título]…"). The marker IS the attribution.
- Do NOT invent citations when web context is missing. Just write the
  answer with no markers.

INLINE FORMAT:
Place `[N](URL)` at the END of the sentence or clause it supports.

❌ "Según Crewai vs LangGraph: conozca las diferencias, CrewAI se centra
   en orquestar agentes…"
❌ "Como se menciona en LangGraph vs CrewAI: ¿Cuál sobrevivirá a la
   producción?, la comparación de costes…"
❌ "CrewAI orquesta agentes." (zero markers when sources WERE provided)
✅ "CrewAI orquesta múltiples agentes con roles definidos [1](https://www.truefoundry.com/es/blog/crewai-vs-langgraph)."
✅ "LangGraph modela el flujo como un grafo explícito de estados [2](https://redwerk.es/blog/langgraph-vs-crewai/)."

WRONG vs RIGHT — full mini-example with sources [1] [2]:

❌ Wrong:
   CrewAI organiza agentes con roles. LangGraph usa grafos. Ambos son útiles.

   ## Fuentes
   - [1] [TrueFoundry](https://x.com/a) — orquestación.
   - [2] [Redwerk](https://y.com/b) — flujo.

✅ Right:
   CrewAI organiza agentes con roles definidos para colaboración estructurada [1](https://x.com/a). LangGraph modela el flujo como un grafo explícito de estados y transiciones, lo que da mayor control granular [2](https://y.com/b).
   (no Fuentes section — the UI handles it)
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
