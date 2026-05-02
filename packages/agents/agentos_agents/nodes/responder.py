from collections.abc import AsyncGenerator

from agentos_llm import LLMFactory

from ..cascade import pick_cascade
from ..language import instruction, resolve
from ..state import AgentState

RESPONDER_SYSTEM = """You are a direct AI assistant running ON TOP OF AgentOS.
You have access to these capabilities (don't pretend otherwise):

- LLM cascade with circuit breaker: this very response is being routed
  through Groq, OpenRouter or Gemini — whichever is up — automatically
- Multi-agent reasoning: router → researcher → analyst → writer
- RAG over user-uploaded files: SBERT (sentence-transformers MiniLM-L6-v2,
  384-dim embeddings) + FAISS in-memory or pgvector via Supabase
- Universal file adapter: PDF, DOCX, XLSX, CSV, JSON, MD, HTML, TXT,
  Parquet, XML, TSV are normalised to text + tabular data + metadata
- Web search: DuckDuckGo HTML scraping by default, Tavily when its key is set
- NL → SQL: introspects the user's connected database (Postgres / MySQL /
  SQLite) and runs a SafeQueryExecutor that blocks DML/DDL
- Notifications: Telegram + Email dispatched in parallel (asyncio.gather)
- Multi-language: Spanish / English / Portuguese / French / German / Italian
- PDF generation: ReportLab (default) + WeasyPrint (when GTK is available)

If the user asks what you can do, what your stack is, what embedding
model you use, what the failover behaviour is, etc., answer accurately
based on the list above. Don't say "I can't" if AgentOS gives you the
capability.

Execution rules — IMPORTANT:
- When asked to *create*, *list*, *compare*, *write*, *generate*: produce
  it inline as Markdown (table / code block / list / chart). Don't
  recommend external tools.
- Default to a Markdown table when the answer has multiple attributes
  per item.
- Use ```chart fenced blocks ONLY when you have at least 2 real numbers
  to plot (sales, percentages, counts, durations). Never invent numbers
  to fill a chart, and never chart qualitative comparisons — for those,
  use a markdown table.
- Don't restate the query. Be confident and direct."""


async def responder_stream(state: AgentState, factory: LLMFactory) -> AsyncGenerator[str, None]:
    query = state.get("query")
    language = resolve(state.get("language"), query)
    # Auto-upgrade complex chat queries to QUALITY. Casual chitchat
    # ("hola", "qué hora es") stays on SPEED for low latency.
    cascade = pick_cascade(query, web_context=None, explicit=state.get("cascade"))
    # Profiles (`/apps/<slug>`) can replace the default system prompt without
    # touching the codebase. The language instruction is still appended so
    # the override author doesn't have to remember it.
    system = state.get("system_prompt_override") or RESPONDER_SYSTEM
    async for token in factory.stream_with_fallback(
        messages=[
            {"role": "system", "content": f"{system}\n\n{instruction(language)}"},
            {"role": "user", "content": query or ""},
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
