# AgentOS

Modular hackathon boilerplate with AI agents, multi-framework frontends, and auto-failover LLM providers. **100% free deployment** (Vercel + Koyeb + Supabase + PocketHost).

> One backend, three frontends, four LLM cascade strategies, full multi-agent reasoning visible in real time.

---

##  Documentación en Español

Si recién llegás, leé estos en orden:

1. **[¿Qué es AgentOS?](docs/es/QUE-ES-AGENTOS.md)** — qué problemas resuelve, para quién es, qué incluye, en lenguaje claro.
2. **[Funcionalidades](docs/es/FUNCIONALIDADES.md)** — catálogo completo de capacidades con ejemplos.
3. **[Guía Rápida](docs/es/GUIA-RAPIDA.md)** — levantarlo en tu compu en 30 minutos.
4. **[Implementación](docs/es/IMPLEMENTACION.md)** — cómo construir TU app encima de AgentOS, con casos reales.

> El resto de la documentación (DEPLOY, USAGE, HACKATHON) está en inglés porque los comandos y nombres de herramientas son universales en ese idioma.

---

## Highlights

- **Multi-agent visible streaming** — every reasoning step (router → researcher → analyst → writer) emits SSE events, displayed live in the UI
- **LLM cascade with circuit breaker** — Groq → OpenRouter → Gemini auto-failover. Free-tier defaults (Groq free + OpenRouter `:free` suffix + Gemini Flash 15 RPM). 3 fails opens the breaker for 60s, then probes again
- **Auto-cascade picker** — the writer/responder default to `speed` for casual chat but auto-upgrade to `quality` (DeepSeek/Qwen/GLM 4.5 Air via OpenRouter) when the query is complex (compare, analyze, list, code) or when web context has fetched body text. No config needed — the chat just gets sharper when the question deserves it
- **Smart web search** — DuckDuckGo HTML scraping (no key) or Tavily (when configured); ad blocks stripped, shopping/spam domains filtered for informational queries (kept for shopping intent), articles older than 180 days dropped on time-sensitive queries, official/authoritative domains (uefa.com, sbert.net, .gov, .edu, etc.) boosted in ranking, full article body extracted from each top result so the writer sees ~1500 chars per source instead of 150-char SERP snippets
- **Configurable embeddings** — default `all-MiniLM-L6-v2` (384-dim, ~80MB, CPU-only, no API key) for plug-and-play. Set `EMBEDDING_MODEL=gemini-embedding-001` to upgrade to multilingual 3072-dim via the same `GEMINI_API_KEY` (free tier ~1500 RPD, 0 MB install)
- **3 frontends, same backend** — SvelteKit / Next.js / Nuxt 3 all dark-mode by default, all consume the same SSE chat API
- **Multi-idioma** — UI y agentes operan en `es` por default y soportan `en/pt/fr/de/it`. Cada request pasa el idioma; los prompts inyectan la directiva al final del system message
- **Universal file adapter** — `packages/files` normaliza PDF · DOCX · XLSX · CSV · JSON · MD · HTML · TXT · TSV · XML · Parquet a texto + tabular antes de RAG/análisis
- **RAG + Web search en agentes** — toggles `use_rag` / `use_web` en cada chat. RAG usa el pipeline pgvector/FAISS; web usa DuckDuckGo (sin key) o Tavily (opcional)
- **2 agent engines** — LangGraph para streaming chat con routing condicional, CrewAI para tareas colaborativas multi-step
- **Rich citation rendering** — when web context is enabled the writer cites each claim as `[N](url)` markdown; the frontend auto-styles numeric link text as superscript pill badges and opens every source in a new tab so clicking doesn't lose the chat. Tables get a 3-button toolbar that copies as styled HTML (preserves colors when pasted into Word/Sheets/Notion), as Markdown, or downloads as `.html`
- **Notifications** — Telegram + Email dispatcher en paralelo
- **NL→SQL** — conectá cualquier DB (Postgres/MySQL/SQLite) y consultala en lenguaje natural con safe-query enforcement
- **PDF export** — botón en cada UI para exportar la última respuesta a PDF (WeasyPrint + Jinja2)
- **Launcher de preview** — `pnpm preview` abre un selector visual para elegir cuál frontend correr
- **All packages are independently deletable** — drop `packages/geo` and nothing else breaks

## Stack

| Layer | Tech |
|------|------|
| Frontends | SvelteKit · Next.js 15 · Nuxt 3 (all Tailwind v4 + TanStack Query) |
| State | Svelte runes · Zustand · Pinia |
| Primary backend | FastAPI + Pydantic + sse-starlette |
| Alt backends | Go (Gin) · Express · NestJS |
| Lightweight backend | PocketBase (Go binary, SQLite) |
| Bot | python-telegram-bot |
| Agents | LangGraph 0.3 (DAG) + CrewAI 0.100 (sequential crews) |
| LLM | Groq SDK · OpenAI SDK (OpenRouter) · google-genai (Gemini) |
| RAG | sentence-transformers (`all-MiniLM-L6-v2` default) **or** Gemini embeddings via API (`gemini-embedding-001`, free tier) — configurable via `EMBEDDING_MODEL`. Vector store: FAISS in-memory or pgvector |
| Data | pandas · numpy · scipy · scikit-learn |
| Geo | geopy (Nominatim) + PostGIS |
| Reports | WeasyPrint + Jinja2 + matplotlib |
| DB | Supabase (Postgres + pgvector + PostGIS + Auth + Realtime) |

## Repo layout

```
apps/
  web-svelte/  SvelteKit frontend  → Vercel
  web-next/  Next.js App Router  → Vercel
  web-vue/  Nuxt 3 frontend  → Vercel / Netlify
  api-go/  Go API (Gin)  → Koyeb
  pocketbase/  PocketBase config  → PocketHost
  telegram/  Telegram bot  → Koyeb
services/
  api/  FastAPI primary backend  → Koyeb
  api-express/  Express alternative
  api-nest/  NestJS alternative
packages/
  llm/  LLM AdapterFactory + cascade + circuit breaker (free-tier models)
  agents/  LangGraph DAG + CrewAI crews + Orchestrator
  rag/  sentence-aware chunking + SBERT embeddings + FAISS / pgvector + filters
  data/  DataFrames + numpy + scipy
  ml/  Anomaly detection + ML pipeline
  geo/  Geocoding + PostGIS + GeoJSON utils
  reports/  WeasyPrint + Jinja2 templates + charts
  notifications/  Telegram + Email dispatcher (multi-channel parallel send)
  database/  Multi-DB adapter (PG/MySQL/SQLite) + safe SELECT + NL→SQL agent
  shared-types/  TypeScript types for all frontends
  ui/  Tailwind preset (colors + fonts + animations)
supabase/
  migrations/  001_initial · 002_pgvector · 003_postgis
docs/  Architecture + system prompt
```

## Quick start

```bash
# 1. Copy env and fill provider keys
cp .env.example .env
# Open .env and set at least one of: GROQ_API_KEY, OPENROUTER_API_KEY, GEMINI_API_KEY

# 2. Install workspace dependencies
pnpm install

# 3. Install Python packages (editable, dev mode)
pip install -e packages/llm[dev]
pip install -e packages/agents
pip install -e packages/rag
pip install -e packages/data
pip install -e packages/ml
pip install -e packages/geo
pip install -e packages/reports
pip install -e services/api[dev]

# 4. Start Postgres + pgvector + PostGIS locally (optional, for full RAG/geo)
docker compose up -d supabase-db

# 5. Start the FastAPI backend
cd services/api && uvicorn app.main:app --reload
# → http://localhost:8000  (interactive docs at /docs)

# 6. Pick a frontend (separate terminal)
pnpm dev:svelte  # → http://localhost:5173
pnpm dev:next  # → http://localhost:3000
pnpm dev:vue  # → http://localhost:3001
```

## API surface

| Endpoint | Method | Description |
|---------|--------|-------------|
| `/health` | GET | Provider availability + circuit-breaker state |
| `/chat/stream` | POST | SSE chat stream (LangGraph router) |
| `/agents/run` | POST | SSE agent run (chat / analysis / research / writing / crew) |
| `/agents/complete` | POST | Sync (non-SSE) completion via cascade |
| `/rag/ingest` | POST | Upload doc → chunk → embed → upsert |
| `/rag/ingest-text` | POST | Programmatic ingest with metadata defaults |
| `/rag/search` | POST | Semantic search top-K with metadata filters |
| `/rag/source/{id}` | DELETE | Remove all chunks of a source doc |
| `/data/upload` | POST | DataFrame summary + describe |
| `/geo/geocode` | POST | Address → lat/lon (Nominatim) |
| `/geo/reverse` | POST | lat/lon → address |
| `/ml/anomalies` | POST | IsolationForest / LOF on uploaded CSV |
| `/reports/generate` | POST | HTML→PDF report with metrics + charts |
| `/notify/send` | POST | Send notification to Telegram + Email in parallel |
| `/notify/channels` | GET | List configured notification channels |
| `/database/schema` | GET | Introspect connected user DB (tables, columns, FKs) |
| `/database/query` | POST | Execute safe SELECT against user DB |
| `/database/nl-query` | POST | Natural language → SQL → results (read-only) |
| `/data/upload` | POST | Universal ingest: PDF/DOCX/CSV/XLSX/JSON/MD/HTML/TXT/... |
| `/rag/ingest` | POST | Same universal adapter, then chunked + embedded into the vector store |

All responses follow `{data, error, meta}`. SSE events:

```ts
{ type: "status",  node: "router",  content: "Classifying intent..." }
{ type: "status",  node: "router",  content: "intent: research" }
{ type: "status",  node: "researcher", content: "5 findings collected" }
{ type: "crew_status",  agent: "analyst",  task: "starting" }
{ type: "token",  content: "Vector " }
{ type: "done" }
{ type: "error",  error: "..." }
```

## LLM cascade strategies

Defined in [`packages/llm/agentos_llm/config.py`](packages/llm/agentos_llm/config.py:5):

| Strategy | Order | When to use |
|----------|-------|-------------|
| `speed` | Groq → OpenRouter → Gemini | chat, classification, fast turns |
| `reasoning` | Gemini → OpenRouter → Groq | analysis, planning, multi-step |
| `cheap` | OpenRouter → Groq → Gemini | high-volume background work |
| `multimodal` | Gemini | images, video, structured docs |
| `quality` | OpenRouter (DeepSeek / Qwen / GLM 4.5 Air / Hermes 405B) → Gemini → Groq | extraction from rich context, comparisons, deep tables |

Always call via `LLMFactory.complete_with_fallback(messages, cascade=...)` — never instantiate adapters directly.

**Auto-pick (writer + responder).** Both nodes use [`pick_cascade()`](packages/agents/agentos_agents/cascade.py:1) when the caller doesn't force one:

1. Caller-set `cascade` wins always.
2. Web context with fetched body → `quality` (so the writer can extract from ~1500-char article bodies).
3. Query matches a complex-intent regex (`compara`, `diferencia`, `analiza`, `lista`, `tabla`, `paso a paso`, `código`, `arquitectura`, `compare`, `step by step`, etc.) or is multi-sentence / >120 chars → `quality`.
4. Otherwise → `speed`.

Result: casual chat ("hola", "qué hora es") stays low-latency; complex questions ("compara langgraph vs crewai", "que equipos en semifinal") auto-upgrade to a stronger model without you flipping a flag.

## Multi-agent flow (LangGraph)

```
START → router ──intent=chat──→ responder ──→ END
  └──intent=research/analysis/writing──→ researcher → analyst → writer → END
```

The runner ([`graphs/runner.py`](packages/agents/agentos_agents/graphs/runner.py:1)) emits SSE events at every node boundary and streams tokens during the final node so the UI sees reasoning in real time.

## Tests

The unit suite is split per package — total is **66 tests** at the time of writing
(LLM factory + circuit breaker, agent graph runner + language + tools, RAG chunking +
FAISS store, notifications dispatcher, database safe-query + introspection, files
factory). To run them all:

```bash
python -m pytest \
  packages/llm/tests \
  packages/rag/tests \
  packages/notifications/tests \
  packages/database/tests \
  packages/files/tests \
  packages/agents/tests \
  -q

# E2E smoke against a running backend (4 checks: health, chat/stream, agents/run, agents/complete)
python scripts/e2e_smoke.py

# Same against prod
BACKEND_URL=https://agentos-api.koyeb.app python scripts/e2e_smoke.py
```

The exact count will drift as tests are added. Treat the number as
illustrative — `pytest --collect-only -q | tail -1` is the source of truth.

CI ([`ci.yml`](.github/workflows/ci.yml)) runs the full per-package suite + Go
build/vet + 3-frontend matrix (Svelte / Next / Vue) on every PR.
CD ([`deploy.yml`](.github/workflows/deploy.yml)) auto-deploys to Koyeb + Vercel
on push to `main` — Svelte / Next / Vue all have a job, gated by their
`VERCEL_*_PROJECT_ID` variable being present.

## Deploy

| Component | Platform | Free tier |
|-----------|----------|-----------|
| `web-svelte`, `web-next`, `web-vue` | Vercel | 100GB bandwidth, 100 deploys/day · the 3 jobs are wired in `deploy.yml` |
| `services/api`, `apps/api-go` | Koyeb | 1 nano instance, 512MB RAM |
| `apps/pocketbase` | PocketHost | 1 instance |
| Postgres + pgvector + PostGIS | Supabase | 500MB DB, 2 projects |
| `apps/telegram` | Koyeb (worker) | 1 nano |

### About the "100% free" claim

The defaults are all free-tier — Groq free plan, OpenRouter `:free`-suffixed
models, Gemini Flash (15 RPM). If a quota runs out the cascade keeps falling
back, and a real budget only shows up if you (a) explicitly switch to a paid
OpenRouter model in `MODEL_OPENROUTER`, or (b) plug in your own paid keys.
Sustained heavy traffic past free-tier limits will degrade gracefully (other
providers in the cascade absorb it) rather than start charging silently.

**Full step-by-step deploy guide → [docs/DEPLOY.md](docs/DEPLOY.md)**
(Supabase + Koyeb + Vercel + GitHub Secrets/Vars + rollback in 30 minutes).

## Conventions

- TypeScript strict, no `any`. Python type hints everywhere. Pydantic models for all I/O.
- API responses: `{data, error, meta}`.
- All LLM calls through `LLMFactory.complete_with_fallback()`.
- Svelte runes / Zustand / Pinia for ephemeral state, TanStack Query for server state.
- No hardcoded secrets — env vars only.
- Each `packages/*` directory is independently deletable.

## Docs

### 🇪🇸 Español (toda la documentación)

Lectura accesible:

| Doc | Contenido |
|-----|-----------|
| [docs/es/QUE-ES-AGENTOS.md](docs/es/QUE-ES-AGENTOS.md) | Qué es, qué problemas resuelve, para quién, qué incluye, qué NO es |
| [docs/es/FUNCIONALIDADES.md](docs/es/FUNCIONALIDADES.md) | Cada feature con ejemplo concreto, cuándo usarlo, limitación honesta |
| [docs/es/GUIA-RAPIDA.md](docs/es/GUIA-RAPIDA.md) | Setup local en 30 minutos: chat, RAG, base de datos, notificaciones |
| [docs/es/IMPLEMENTACION.md](docs/es/IMPLEMENTACION.md) | Cómo construir TU app encima: casos reales, código, anti-patrones |

Referencia técnica en español:

| Doc | Contenido |
|-----|-----------|
| [docs/es/USO.md](docs/es/USO.md) | Referencia de la API con curl, patrones por framework, cómo extender |
| [docs/es/DESPLIEGUE.md](docs/es/DESPLIEGUE.md) | Despliegue paso a paso con `gh` CLI, secrets/vars, rollback, troubleshooting |
| [docs/es/HACKATHON.md](docs/es/HACKATHON.md) | Camino MVP en 90 min, patrones de customización, script de demo |
| [docs/es/ARQUITECTURA.md](docs/es/ARQUITECTURA.md) | Diagrama completo, data flow, breakdown de módulos |
| [docs/es/SYSTEM-PROMPT.md](docs/es/SYSTEM-PROMPT.md) | Prompt de ingeniero senior para trabajar el proyecto con cualquier LLM |
| [CLAUDE.md](CLAUDE.md) | Reglas del proyecto que ve Claude Code |

### 🇬🇧 English (originals)

Los archivos en `docs/` sin `/es/` son los originales — mismo contenido, headers
en inglés. Si preferís leer todo en español, andá directo a `docs/es/`.

## What's next — building YOUR app on top

This repo is the **platform**. Your hackathon app is what you build on it. The flow:

```
1. gh repo fork agentos --clone
2. Customize the agent system prompt (packages/agents/agentos_agents/nodes/responder.py)
3. Customize the UI branding (apps/web-<svelte|next|vue>/src/routes/+page.svelte)
4. (Optional) Wire your domain: RAG corpus, custom endpoint, custom crew
5. Deploy with the GitHub Actions workflow
```

See [docs/HACKATHON.md](docs/HACKATHON.md) for the full guide — it's tuned for shipping a demo in 90 minutes.

## License

MIT
