# AgentOS — Arquitectura completa (referencia técnica en español)

## Visión general

AgentOS es un monorepo modular diseñado para ganar hackatones. Provee una base reutilizable con múltiples frontends, backends, agentes IA con failover automático, y módulos de ciencia de datos. Todo deployable en plataformas 100% gratuitas.

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTENDS                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   SvelteKit  │  │   Next.js    │  │   Nuxt 3     │          │
│  │  Svelte stores│  │   Zustand   │  │   Pinia      │          │
│  │  TanStack Q  │  │  TanStack Q  │  │  TanStack Q  │          │
│  │   Tailwind   │  │   Tailwind   │  │   Tailwind   │          │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘          │
│         │ Vercel          │ Vercel          │ Netlify           │
└─────────┼─────────────────┼─────────────────┼───────────────────┘
          │ SSE/REST        │ SSE/REST        │ SSE/REST
┌─────────┼─────────────────┼─────────────────┼───────────────────┐
│         ▼                 ▼                 ▼                   │
│  ┌─────────────────────────────────────────────────┐            │
│  │              API LAYER (Koyeb)                   │            │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐      │            │
│  │  │ FastAPI   │  │  Go Gin  │  │ Express  │      │            │
│  │  │ (primary) │  │ (perf)   │  │ (alt)    │      │            │
│  │  └────┬──────┘  └────┬─────┘  └──────────┘      │            │
│  │       │              │                           │            │
│  │       ▼              ▼                           │            │
│  │  ┌──────────────────────────────────────┐       │            │
│  │  │         SHARED PACKAGES              │       │            │
│  │  │  ┌─────┐ ┌────────┐ ┌─────┐        │       │            │
│  │  │  │ LLM │ │ Agents │ │ RAG │        │       │            │
│  │  │  │Factory│ │LangGraph│ │SBERT│       │       │            │
│  │  │  │     │ │+CrewAI │ │FAISS│        │       │            │
│  │  │  └──┬──┘ └────────┘ └─────┘        │       │            │
│  │  │     │                               │       │            │
│  │  │  ┌──┴────────────────────────────┐  │       │            │
│  │  │  │  Cascade + Circuit Breaker    │  │       │            │
│  │  │  │  Groq → OpenRouter → Gemini   │  │       │            │
│  │  │  └───────────────────────────────┘  │       │            │
│  │  │                                      │       │            │
│  │  │  ┌──────┐ ┌────┐ ┌─────┐ ┌───────┐ │       │            │
│  │  │  │ Data │ │ ML │ │ Geo │ │Reports│ │       │            │
│  │  │  │pandas│ │IsoF│ │PostG│ │  PDF  │ │       │            │
│  │  │  └──────┘ └────┘ └─────┘ └───────┘ │       │            │
│  │  └──────────────────────────────────────┘       │            │
│  └─────────────────────────────────────────────────┘            │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐                             │
│  │  PocketBase  │  │  Telegram    │                             │
│  │  PocketHost  │  │    Bot       │                             │
│  └──────────────┘  └──────────────┘                             │
└──────────────────────────────────────────────────────────────────┘
          │
┌─────────▼─────────────────────────────────────────────────────────┐
│                     DATA LAYER                                     │
│  ┌─────────────────────────────────────────┐                      │
│  │          Supabase (free tier)            │                      │
│  │  PostgreSQL + pgvector + PostGIS         │                      │
│  │  Auth + Realtime + Row Level Security    │                      │
│  └─────────────────────────────────────────┘                      │
└────────────────────────────────────────────────────────────────────┘
```

## Flujo de Datos

### Chat Request (SSE Streaming)
```
1. Usuario escribe mensaje en Chat UI
2. Frontend (Svelte store / Zustand) → POST /api/chat (proxy local)
3. SvelteKit/Next.js proxy → POST FastAPI /chat/stream
4. FastAPI → Orchestrator.run(message)
5. Orchestrator decide: LangGraph (chat) vs CrewAI (analysis)
6. Orchestrator → LLMFactory.get("speed") → Groq adapter
   ↓ [si Groq falla → CircuitBreaker → OpenRouter → Gemini]
7. Adapter.stream() → tokens SSE
8. FastAPI → SSE events → proxy → frontend
9. Svelte store / Zustand actualiza UI en tiempo real:
   - {type: "status", node: "thinking"} → indicador "pensando..."
   - {type: "token", content: "..."} → texto aparece caracter por caracter
   - {type: "done"} → mensaje completo, guardar en historial
```

### RAG Ingest + Query
```
Ingest:
1. POST /rag/ingest (archivo)
2. chunking.py → split texto en chunks de 500 words con overlap
3. embeddings.py → SBERT encode → vectores 384-dim
4. VectorStoreFactory → faiss (dev) / pgvector (prod) → upsert

Query:
1. POST /rag/search {query, top_k}
2. embeddings.py → encode query
3. VectorStore.search() → top-K resultados por cosine similarity
4. Return [{content, score, metadata}]
```

### LLM Failover
```
Request → LLMFactory.complete_with_fallback(messages, cascade="speed")
  │
  ├── Groq (fast, ~200ms first token)
  │   ├── Success → record_success() → return response
  │   └── Fail (rate limit / timeout / error)
  │       └── circuit_breaker.record_failure()
  │           ├── failures < 3 → try next
  │           └── failures >= 3 → open circuit for 60s
  │
  ├── OpenRouter (fallback, routes to cheap models)
  │   ├── Success → return response
  │   └── Fail → record_failure() → try next
  │
  ├── Gemini 2.5 (last resort, good reasoning)
  │   ├── Success → return response
  │   └── Fail → AllProvidersFailedError
  │
  └── All failed → return error to user
```

## Módulos en Detalle

### packages/llm — LLM AdapterFactory
- `base.py`: ABC con `complete()`, `stream()`, `structured_output()`
- `factory.py`: Cascade strategies (speed/reasoning/cheap/multimodal) + `complete_with_fallback()`
- `failover.py`: CircuitBreaker con threshold configurable
- `adapters/`: Groq (SDK nativo), OpenRouter (via OpenAI SDK), Gemini (google-genai)

### packages/agents — LangGraph + CrewAI
- `orchestrator.py`: Punto de entrada. Analiza intent → elige motor
- `graphs/`: LangGraph DAGs para flujos con estado (chat, research)
- `crews/`: CrewAI crews con `BaseCrew` que integra LLMFactory
- `state.py`: TypedDict compartido entre nodos

### packages/rag — RAG Pipeline
- `pipeline.py`: `ingest(docs)` → chunk → embed → store. `query(question)` → embed → search
- `embeddings.py`: SBERT `all-MiniLM-L6-v2` (~90MB, 384-dim)
- `vectorstore/`: Factory pattern → FAISSStore (dev) / PgVectorStore (prod)

### packages/data — DataFrames + Cálculos
- `frames.py`: Load CSV/Excel/JSON/Parquet, summary stats
- `vectorized.py`: Normalize, standardize, cosine similarity, moving average
- `algebra.py`: Linear regression, interpolation, SVD, PCA, solve systems

### packages/ml — Machine Learning
- `anomaly.py`: IsolationForest + LOF con fit/predict interface
- `pipeline.py`: Generic train/predict/evaluate con auto-detect classification vs regression

### packages/geo — Geoespacial
- `geocoding.py`: Nominatim (gratis) async geocode/reverse
- `postgis.py`: Spatial queries (radius search, bbox)
- `utils.py`: Haversine distance, GeoJSON conversion

### packages/reports — PDF Reports
- `generator.py`: Jinja2 template → HTML → WeasyPrint → PDF bytes
- `charts.py`: matplotlib figures → base64 embeddable en HTML
- `templates/`: Base layout + report template con métricas, tablas, gráficos

## Deploy

| Servicio | Plataforma | Tier | Límites |
|----------|-----------|------|---------|
| SvelteKit / Next.js | Vercel | Free | 100GB bandwidth, 100 deploys/day |
| Nuxt 3 | Netlify / Vercel | Free | 100GB bandwidth |
| FastAPI + Agents | Koyeb | Free nano | 1 instance, 512MB RAM |
| Go API | Koyeb | Free nano | Shared with FastAPI or separate |
| PocketBase | PocketHost | Free | 1 instance |
| PostgreSQL + pgvector | Supabase | Free | 500MB DB, 2 projects |
| Telegram Bot | Koyeb | Free | Same instance as API |

## Tecnologías Clave

| Categoría | Tecnología | Versión | Uso |
|-----------|-----------|---------|-----|
| Runtime | Node.js | 20+ | Frontend builds |
| Runtime | Python | 3.12+ | Backend + ML |
| Runtime | Go | 1.23+ | High-perf API |
| Package Manager | pnpm | 9+ | Monorepo workspaces |
| Build | Turborepo | Latest | Cache + parallel builds |
| Frontend | SvelteKit | 2 | Primary frontend |
| Frontend | Next.js | 15 | React alternative |
| Frontend | Nuxt | 3 | Vue alternative |
| CSS | Tailwind CSS | 4 | All frontends |
| State | Svelte stores | Built-in | Client state (Svelte) |
| State | Zustand | 5+ | Client state (React) |
| State | Pinia | 2+ | Client state (Vue) |
| Server State | TanStack Query | 5+ | All frontends |
| Backend | FastAPI | 0.115+ | Primary API |
| Backend | Gin | 1.10+ | Go API |
| AI | LangGraph | 0.3+ | Agent graphs |
| AI | CrewAI | 0.100+ | Agent crews |
| LLM | Groq SDK | 0.13+ | Speed provider |
| LLM | OpenAI SDK | 1.60+ | OpenRouter adapter |
| LLM | google-genai | 1.0+ | Gemini adapter |
| Embeddings | sentence-transformers | 3.0+ | SBERT |
| Vector | faiss-cpu | 1.9+ | Local dev |
| Vector | pgvector | 0.7+ | Production (via Supabase) |
| Data | pandas | 2.2+ | DataFrames |
| Data | numpy | 2.0+ | Vectorized calc |
| Data | scipy | 1.14+ | Linear algebra |
| ML | scikit-learn | 1.6+ | Anomaly detection |
| Geo | geopy | 2.4+ | Geocoding |
| Geo | PostGIS | 3.4+ | Spatial queries |
| Reports | WeasyPrint | 63+ | HTML → PDF |
| Reports | Jinja2 | 3.1+ | Templates |
| Reports | matplotlib | 3.9+ | Charts |
| DB | Supabase | Latest | PostgreSQL + Auth |
| DB | PocketBase | 0.23+ | Lightweight backend |
| Bot | python-telegram-bot | 21+ | Telegram |
