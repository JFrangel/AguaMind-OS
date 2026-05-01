import json

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from agentos_agents import Orchestrator

router = APIRouter()


class AgentRunRequest(BaseModel):
    task: str
    context_type: str = "analysis"
    engine: str | None = None
    cascade: str | None = None
    crew: str | None = None
    context: dict = {}


class CompleteRequest(BaseModel):
    messages: list[dict]
    cascade: str = "speed"
    temperature: float = 0.7
    max_tokens: int = 2000


@router.post("/run")
async def run_agent(body: AgentRunRequest, request: Request):
    llm_factory = request.app.state.llm_factory
    orchestrator = Orchestrator(llm_factory=llm_factory)

    async def event_generator():
        ctx = {"type": body.context_type, **body.context}
        if body.engine:
            ctx["engine"] = body.engine
        if body.cascade:
            ctx["cascade"] = body.cascade
        if body.crew:
            ctx["crew"] = body.crew
        async for event in orchestrator.run(body.task, ctx):
            yield {"data": json.dumps(event)}

    return EventSourceResponse(event_generator())


@router.post("/complete")
async def complete(body: CompleteRequest, request: Request):
    """Sync completion endpoint used by api-go and any non-streaming client.

    Goes through LLMFactory so the cascade + circuit breaker apply. Returns
    a structured 503 when every provider in the cascade is unavailable so
    callers can branch on `error` rather than parse a stack trace.
    """
    from agentos_llm.factory import AllProvidersFailedError

    factory = request.app.state.llm_factory
    try:
        result = await factory.complete_with_fallback(
            messages=body.messages,
            cascade=body.cascade,
            temperature=body.temperature,
            max_tokens=body.max_tokens,
        )
    except AllProvidersFailedError as e:
        return JSONResponse(
            status_code=503,
            content={"data": None, "error": "all_providers_failed", "meta": {"detail": str(e)}},
        )

    return {
        "data": {
            "content": result.content,
            "provider": result.provider.value,
            "model": result.model,
            "usage": result.usage,
            "latency_ms": result.latency_ms,
        },
        "error": None,
    }
