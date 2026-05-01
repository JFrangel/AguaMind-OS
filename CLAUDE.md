# AgentOS

Modular hackathon boilerplate with AI agents, multi-framework frontends, and auto-failover LLM providers. 100% free deployment.

## Stack
- **Frontends**: SvelteKit (Svelte stores), Next.js (Zustand), Nuxt 3 (Pinia) — all with Tailwind + TanStack Query
- **Backends**: FastAPI (Python), Go Gin/Fiber, Express, NestJS, PocketBase
- **AI**: LangGraph + CrewAI agents with LLMFactory cascade (Groq → OpenRouter → Gemini)
- **Data**: pgvector + FAISS (RAG), pandas/polars, scikit-learn, PostGIS, WeasyPrint PDFs
- **DB**: Supabase (PostgreSQL + pgvector + PostGIS + auth + realtime)
- **Deploy**: Vercel (frontends), Koyeb (backends), PocketHost (PocketBase), Supabase (DB)

## Monorepo Layout
- `apps/web-svelte` — SvelteKit frontend (Vercel)
- `apps/web-next` — Next.js + React frontend (Vercel)
- `apps/web-vue` — Nuxt 3 frontend (Vercel/Netlify)
- `apps/api-go` — Go API with Gin/Fiber (Koyeb)
- `apps/pocketbase` — PocketBase backend (PocketHost)
- `apps/telegram` — Telegram bot
- `services/api` — FastAPI principal (Koyeb)
- `services/api-express` — Express.js alternative
- `services/api-nest` — NestJS alternative
- `packages/llm` — LLM AdapterFactory with cascade + circuit breaker failover
- `packages/agents` — LangGraph + CrewAI orchestration
- `packages/rag` — RAG pipeline (pgvector/FAISS + SBERT)
- `packages/data` — DataFrames, numpy, scipy
- `packages/ml` — Anomaly detection, ML pipeline
- `packages/geo` — Geocoding + PostGIS
- `packages/reports` — PDF generation (WeasyPrint + Jinja2)
- `packages/notifications` — Telegram + Email dispatcher (multi-channel parallel send)
- `packages/database` — Multi-DB adapter (PG/MySQL/SQLite) + safe SELECT executor + NL→SQL
- `packages/shared-types` — Shared TypeScript types
- `packages/ui` — Shared Tailwind preset

## Commands
- `pnpm dev` — start all frontend dev servers
- `pnpm dev:svelte` — SvelteKit only
- `pnpm dev:next` — Next.js only
- `pnpm build` — build all packages
- `cd services/api && uvicorn app.main:app --reload` — FastAPI dev
- `cd apps/api-go && go run cmd/server/main.go` — Go API dev
- `docker compose up supabase-db` — local PostgreSQL + pgvector + PostGIS

## Conventions
- TypeScript strict mode, no `any`
- Python: type hints everywhere, Pydantic models for all I/O
- Svelte stores for ephemeral state, TanStack Query for server state
- Zustand for React client state, Pinia for Vue client state
- All API responses: `{data, error, meta}` shape
- LLM calls always through `LLMFactory.complete_with_fallback()`
- Never hardcode API keys — always from env
- Python imports: absolute paths (`from agentos_llm.factory import ...`)
- Each package is independently deletable without breaking others
