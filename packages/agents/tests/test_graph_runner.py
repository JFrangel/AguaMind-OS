"""Integration tests for the LangGraph chat runner.

Verifies the runner emits the correct event sequence for both intents
(chat → responder) and (research → researcher → analyst → writer) using
a scripted adapter so no LLM calls happen.
"""
import json

import pytest

from agentos_agents.graphs import run_graph_stream


def _router_for(intent: str) -> str:
    return json.dumps({"intent": intent, "plan": ["step a", "step b"]})


@pytest.mark.asyncio
async def test_chat_intent_takes_responder_path(make_factory, scripted_adapter):
    def router(messages):
        last_user = next((m for m in reversed(messages) if m["role"] == "user"), None)
        # Router prompt always sends the user query as the user message
        if last_user and "classify" not in last_user.get("content", "").lower():
            return _router_for("chat")
        return _router_for("chat")

    adapter = scripted_adapter(route=router, stream_text="Hi there friend.")
    factory = make_factory(adapter)

    events = [e async for e in run_graph_stream("hello", factory)]
    types = [e["type"] for e in events]
    nodes = [e.get("node") for e in events if e["type"] == "status"]

    assert "router" in nodes
    assert "responder" in nodes
    assert "researcher" not in nodes
    assert types[-1] == "done"
    assert any(e["type"] == "token" for e in events)


@pytest.mark.asyncio
async def test_research_intent_runs_full_pipeline(make_factory, scripted_adapter):
    call_count = {"n": 0}

    def router(messages):
        call_count["n"] += 1
        if call_count["n"] == 1:
            return _router_for("research")
        if call_count["n"] == 2:
            return "- Vector DBs use ANN\n- pgvector is built on Postgres\n- FAISS is in-memory"
        return "Vector DBs trade recall for latency. pgvector wins on operational simplicity."

    adapter = scripted_adapter(route=router, stream_text="Final response token by token.")
    factory = make_factory(adapter)

    events = [e async for e in run_graph_stream("explain vector dbs", factory)]
    nodes = [e.get("node") for e in events if e["type"] == "status"]

    assert "router" in nodes
    assert "researcher" in nodes
    assert "analyst" in nodes
    assert "writer" in nodes
    assert "responder" not in nodes
    assert events[-1]["type"] == "done"
    assert any(e["type"] == "token" for e in events)


@pytest.mark.asyncio
async def test_router_failure_emits_error(make_factory, scripted_adapter):
    class FailingAdapter(scripted_adapter):
        async def complete(self, messages, **kwargs):
            raise RuntimeError("boom")

    adapter = FailingAdapter(route=lambda m: "")
    factory = make_factory(adapter)

    events = [e async for e in run_graph_stream("hi", factory)]
    error_events = [e for e in events if e["type"] == "error"]
    assert error_events, "expected an error event when router fails"
    # The error event may surface as a friendly AllProvidersFailed payload
    # (when the cascade has only one adapter and it raises) or as a plain
    # `<stage> failed: …` message. Either way the stage should be set so
    # callers can route on it without parsing free-form text.
    assert error_events[0].get("stage") == "router failed" or "router failed" in (
        error_events[0].get("error") or ""
    )


@pytest.mark.asyncio
async def test_router_emits_intent_status(make_factory, scripted_adapter):
    adapter = scripted_adapter(route=lambda m: _router_for("chat"))
    factory = make_factory(adapter)

    events = [e async for e in run_graph_stream("hi", factory)]
    # The status content is i18n'd ("intent:" / "intención:" / etc). The
    # robust check is: a router status event whose content contains the
    # actual intent string ("chat") emitted right after classification.
    intent_events = [
        e
        for e in events
        if e["type"] == "status"
        and e.get("node") == "router"
        and "chat" in e.get("content", "").lower()
    ]
    assert intent_events, "router should emit a follow-up status with the intent"
