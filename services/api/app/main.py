import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


def _load_env_file() -> None:
    """Lightweight .env loader run before settings + LLM adapters import os.environ.

    Walks up from this file looking for the first `.env` and sets any missing
    keys. Does NOT overwrite existing env vars (so docker/koyeb env wins).
    """
    here = Path(__file__).resolve()
    for parent in here.parents:
        env_path = parent / ".env"
        if env_path.is_file():
            for line in env_path.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, _, value = line.partition("=")
                key = key.strip()
                value = value.strip().strip("'").strip('"')
                if key and key not in os.environ:
                    os.environ[key] = value
            return


_load_env_file()

from .config import settings  # noqa: E402  — must follow _load_env_file
from .middleware import RateLimitMiddleware  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    from agentos_llm import LLMFactory
    from agentos_notifications import NotificationDispatcher
    from agentos_rag import RAGPipeline

    app.state.llm_factory = LLMFactory()
    app.state.notifier = NotificationDispatcher()
    # One pipeline per process: shared between /rag/* (upload, search) and the
    # agents' RAG tool. Without this they used to be two separate FAISS stores
    # in memory — uploads went to one, chat queried the other empty one.
    app.state.rag_pipeline = RAGPipeline()

    if settings.supabase_url and settings.supabase_service_key:
        from .services.supabase_client import SupabaseService

        app.state.supabase = SupabaseService(
            settings.supabase_url, settings.supabase_service_key
        )
    else:
        app.state.supabase = None

    yield


app = FastAPI(
    title="AgentOS API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(RateLimitMiddleware, requests_per_minute=settings.rate_limit_per_minute)

from .routers import (
    agents,
    agent_water,
    chat,
    data,
    database,
    geo,
    health,
    mitigation,
    ml,
    notify,
    profiles,
    rag,
    reports,
    water,
)


@app.get("/", tags=["meta"])
async def root() -> dict:
    """Friendly landing for `GET /`. Hitting the FastAPI root with no path
    used to return `{"detail":"Not Found"}`, which is technically correct
    but unhelpful when the user is just checking the URL is alive.

    Returns a small index of useful entry points so curl/Postman/browser
    immediately tell you what's available.
    """
    return {
        "service": "AgentOS API",
        "version": "0.1.0",
        "docs": "/docs",
        "redoc": "/redoc",
        "openapi": "/openapi.json",
        "health": "/health",
        "endpoints": {
            "chat": "POST /chat/stream",
            "agents": "POST /agents/run · POST /agents/complete",
            "rag": "POST /rag/ingest · POST /rag/search · DELETE /rag/source/{id}",
            "data": "POST /data/upload · POST /data/analyze",
            "geo": "POST /geo/geocode · POST /geo/reverse",
            "ml": "POST /ml/anomalies",
            "reports": "POST /reports/generate",
            "notify": "POST /notify/send · GET /notify/channels",
            "database": "GET /database/schema · POST /database/query · POST /database/nl-query",
            "profiles": "GET /profiles · GET /profiles/{slug}",
            "water": "GET /water/reading · GET /water/status · GET /water/history · GET /water/report/daily · POST /water/simulate · POST /water/ingest",
            "water_agent": "POST /water/agent/start · POST /water/agent/stop · GET /water/agent/status · POST /water/agent/cycle · GET /water/agent/stream",
        },
    }


app.include_router(health.router)
app.include_router(chat.router, prefix="/chat", tags=["chat"])
app.include_router(agents.router, prefix="/agents", tags=["agents"])
app.include_router(rag.router, prefix="/rag", tags=["rag"])
app.include_router(data.router, prefix="/data", tags=["data"])
app.include_router(geo.router, prefix="/geo", tags=["geo"])
app.include_router(ml.router, prefix="/ml", tags=["ml"])
app.include_router(reports.router, prefix="/reports", tags=["reports"])
app.include_router(notify.router, prefix="/notify", tags=["notifications"])
app.include_router(database.router, prefix="/database", tags=["database"])
app.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
app.include_router(water.router,       prefix="/water", tags=["water"])
app.include_router(agent_water.router, prefix="/water", tags=["water-agent"])
app.include_router(mitigation.router,  prefix="/water", tags=["mitigation"])
