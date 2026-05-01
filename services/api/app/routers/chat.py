import json

from fastapi import APIRouter, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

from agentos_agents import Orchestrator
from agentos_agents.tools import RAGTool

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    context_type: str = "chat"
    language: str | None = None
    use_rag: bool = False
    use_web: bool = False
    cascade: str | None = None
    # Profiles (/apps/<slug>) pass their domain prompt here. The router/
    # researcher/analyst keep their generic prompts; only the responder/
    # writer (the user-facing voice) get replaced.
    system_prompt_override: str | None = None


@router.post("/stream")
async def chat_stream(body: ChatRequest, request: Request):
    llm_factory = request.app.state.llm_factory

    # Build a RAG tool that talks to the SAME pipeline /rag/ingest writes to.
    # Without this the agent had its own empty FAISS store — uploads went one
    # way, the researcher queried the other.
    pipeline = request.app.state.rag_pipeline

    async def rag_query(question: str, top_k: int) -> list[dict]:
        return await pipeline.query(question, top_k=top_k)

    rag_tool = RAGTool(query_fn=rag_query)
    orchestrator = Orchestrator(llm_factory=llm_factory, rag_tool=rag_tool)

    async def event_generator():
        ctx = {
            "type": body.context_type,
            "use_rag": body.use_rag,
            "use_web": body.use_web,
        }
        if body.language:
            ctx["language"] = body.language
        if body.cascade:
            ctx["cascade"] = body.cascade
        if body.system_prompt_override:
            ctx["system_prompt_override"] = body.system_prompt_override
        async for event in orchestrator.run(body.message, ctx):
            yield {"data": json.dumps(event)}

    return EventSourceResponse(event_generator())
