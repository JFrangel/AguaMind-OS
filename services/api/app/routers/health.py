import time

from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health")
async def health(request: Request):
    llm_factory = request.app.state.llm_factory
    status_info = llm_factory.get_status()

    any_available = any(
        p.get("available") for p in status_info["providers"].values()
    )

    return {
        "status": "ok" if any_available else "degraded",
        "providers": status_info["providers"],
        "timestamp": int(time.time()),
    }
