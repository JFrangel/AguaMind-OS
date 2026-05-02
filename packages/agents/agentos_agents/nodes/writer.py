import datetime
from collections.abc import AsyncGenerator

from agentos_llm import LLMFactory

from ..cascade import pick_cascade
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

Use the full context — but ONLY what the sources actually say.

When the sources contain rich related details (matchup pairings,
aggregate scores, dates, venues, names, numbers, prices, versions,
percentages), include them in the answer. The bare-minimum answer is
rarely what the user wants when sources have more.

But never invent structure or values that aren't explicitly in the
sources. The most common failure mode is fabricating tabular detail
the user wants but that the sources don't confirm:

  ❌ "El article describes 4 cuartos finals. I'll create a 4-row table
     `| Cruce | Ida | Vuelta |` with each cuartos pair, calling them
     'semifinal'." (mistakes cuartos elimination for semi matchups)
  ❌ Table with `?` / `-` placeholders for columns the sources don't fill.
  ❌ Inventing scores, dates, percentages, prices that "look reasonable".

  ✅ If sources name 4 advancing teams but DON'T explicitly state the
     semi pairings, just list the 4 teams and note "los cruces aún no
     están detallados en las fuentes consultadas". Don't make pairs up.
  ✅ If sources have aggregate scores for cuartos but not semis, build
     a "Cuartos resultados" table — labeling it correctly — and a
     separate one-paragraph note about who advanced to semis.
  ✅ When a column would be 50%+ empty, drop it instead of padding.

Same principle for tech: if vector-DB sources mention 6 products with
prices for 3 of them, give pricing for 3 and leave it off the others.
Don't write "$70" / "$N/A" rows.

The writer's job is to ORGANIZE what the sources say, not to fill in
gaps with plausible-looking guesses.

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

Don't include sections, tables, COLUMNS, or rows you'd fill with
placeholders like "No disponible", "No aplica", "N/A", "—", "-",
or "(no data)". If only some rows of a column have a value, drop
the whole column — half-empty columns waste the user's attention.
A single comparison table is usually enough — don't add a
"## Resumen de la comparativa" repeating the same data.

When the answer is fundamentally numerical (rankings, time series,
distributions), include a chart by emitting a fenced block tagged
`chart`. Only do this when you have ≥2 real numerical data points
from the query/findings — never invent numbers, and never chart
qualitative comparisons (use a table for those):

```chart
{"type":"bar","title":"Ventas por mes","data":[["Ene",120],["Feb",95],["Mar",140]]}
```

Chart types: "bar" (categorical), "line" (sequential), "area".
Data is an array of [label, value] tuples with NUMERIC values.
Optional: `title`, `subtitle`, `unit`.

Tone: confident, direct. Don't apologise for limitations unless you
genuinely can't do the task. Don't restate the query.
"""

WRITER_SOURCES_DIRECTIVE = """When the user-provided context includes web sources, cite specific
factual claims inline using markdown link syntax `[N](URL)` placed at
the END of the supported clause. The N must match the number shown in
the "Web sources" block of the user message — do not invent numbers
beyond what's listed there.

Example:
    Pinecone es la solución más fácil de usar pero la más cara [1](https://datacamp.com/blog/vector-dbs).

Don't write a list of sources at the end of the answer under ANY form.
That includes:
  - Headings: `## Fuentes`, `## Referencias`, `## Sources`,
    `## Bibliografía`, `## Enlaces`.
  - Plain text: `Referencias:` / `Fuentes:` followed by URLs.
  - Bold standalone: `**Fuentes**`, `**References**`.
  - **Markdown table at the end with columns like `| Fuente | URL |`,
    `| # | Source |`, or any other "here are the links" tabular form.**
  - Bullet list of URLs at the end.
The chat UI already shows every source as a numbered pill under the
message — duplicating that list in prose is redundant noise. The ONLY
way to surface a source in your answer is via inline `[N](URL)`.

Don't inline source titles or names as prose ("Según [titulo del
artículo]…", "Según [Source Name]…", "Como se menciona en X…"). The
[N](URL) marker is the attribution.
"""


def _format_web_block(web: list[dict]) -> str:
    """Render the web search context as a numbered block for the user message.

    When the search adapter has fetched the article body (DuckDuckGo path
    via _enrich_results), we surface it instead of the SERP snippet —
    snippets are typically 150 chars and end with "..." so they don't
    contain the actual answer. We also include the article publication
    date (when available) so the writer can prefer recent sources and
    flag stale ones — critical for time-sensitive queries where an old
    speculative article can otherwise be confidently quoted as truth.
    """
    today = datetime.date.today().isoformat()
    lines = [
        f"Web sources (today is {today}; for time-sensitive facts, prefer "
        f"recent dates and treat much-older sources as potentially stale "
        f"— use the most recent source when they disagree):"
    ]
    for i, item in enumerate(web, 1):
        title = item.get("title") or "(untitled)"
        url = item.get("url") or ""
        published = (item.get("published") or "").strip()
        body = (item.get("body") or "").strip().replace("\n", " ")
        snippet = (item.get("snippet") or "").strip().replace("\n", " ")
        # Prefer body (article extract) over snippet (DDG SERP teaser).
        text = body or snippet
        if len(text) > 1500:
            text = text[:1497] + "…"
        date_tag = f"  ·  published: {published}" if published else ""
        lines.append(f"[{i}] {title}{date_tag}\n    URL: {url}\n    {text}")
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

    # Cascade choice: pick_cascade auto-upgrades to QUALITY when the
    # web context has body text OR the query itself is complex (long,
    # multi-sentence, comparison/list/analysis/code intent). State-level
    # override still wins so callers can force a specific cascade.
    cascade = pick_cascade(query, web_context, explicit=state.get("cascade"))
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
