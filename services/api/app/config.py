from pathlib import Path

from pydantic_settings import BaseSettings


def _candidate_env_files() -> tuple[str, ...]:
    """Walk up from the package looking for `.env`.

    Lets uvicorn run from any working directory (services/api/, repo root,
    or via `--app-dir`) without requiring an explicit cwd.
    """
    here = Path(__file__).resolve()
    paths = []
    for parent in here.parents:
        candidate = parent / ".env"
        paths.append(str(candidate))
        if parent.name == "":
            break
    return tuple(paths)


class Settings(BaseSettings):
    environment: str = "development"
    debug: bool = True

    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_service_key: str = ""
    database_url: str = "postgresql://postgres:postgres@localhost:5432/agentos"

    groq_api_key: str = ""
    openrouter_api_key: str = ""
    gemini_api_key: str = ""
    llm_default_cascade: str = "speed"

    vector_backend: str = "faiss"

    backend_url: str = "http://localhost:8000"
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:3000", "http://localhost:3001"]

    auth_required: bool = False
    rate_limit_per_minute: int = 60

    model_config = {
        "env_file": _candidate_env_files(),
        "extra": "ignore",
    }


settings = Settings()
