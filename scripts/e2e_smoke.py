#!/usr/bin/env python3
"""End-to-end smoke test for the AgentOS FastAPI backend.

Hits the public endpoints in sequence and asserts each contract. Prints a
PASS/FAIL summary and exits non-zero on any failure so it can run in CI or a
local pre-deploy check.

Usage:
    python scripts/e2e_smoke.py                       # localhost:8000
    BACKEND_URL=https://agentos-api.koyeb.app python scripts/e2e_smoke.py
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any, Callable

import urllib.error
import urllib.request

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
TIMEOUT = float(os.getenv("E2E_TIMEOUT", "20"))


class CheckResult:
    def __init__(self, name: str):
        self.name = name
        self.ok = False
        self.detail = ""
        self.elapsed_ms = 0.0


def _fetch(method: str, path: str, body: dict | None = None) -> tuple[int, bytes]:
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"{BACKEND_URL}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"} if data else {},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.status, resp.read()


def _read_sse_events(path: str, body: dict, max_events: int = 50) -> list[dict]:
    data = json.dumps(body).encode()
    req = urllib.request.Request(
        f"{BACKEND_URL}{path}",
        data=data,
        method="POST",
        headers={"Content-Type": "application/json", "Accept": "text/event-stream"},
    )
    events: list[dict] = []
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        buffer = b""
        for chunk in resp:
            buffer += chunk
            while b"\n" in buffer:
                line, _, buffer = buffer.partition(b"\n")
                line = line.strip()
                if not line.startswith(b"data: "):
                    continue
                try:
                    events.append(json.loads(line[6:].decode()))
                except json.JSONDecodeError:
                    continue
                if len(events) >= max_events or events[-1].get("type") in ("done", "error"):
                    return events
    return events


def check(name: str, fn: Callable[[CheckResult], None]) -> CheckResult:
    result = CheckResult(name)
    start = time.monotonic()
    try:
        fn(result)
        result.ok = True
    except AssertionError as e:
        result.detail = f"assertion: {e}"
    except urllib.error.URLError as e:
        result.detail = f"network: {e}"
    except Exception as e:
        result.detail = f"{type(e).__name__}: {e}"
    result.elapsed_ms = (time.monotonic() - start) * 1000
    return result


def health_check(r: CheckResult) -> None:
    status, body = _fetch("GET", "/health")
    assert status == 200, f"status={status}"
    payload = json.loads(body)
    assert "providers" in payload, "missing providers key"
    assert payload.get("status") in ("ok", "degraded"), f"unexpected status={payload.get('status')}"
    r.detail = f"status={payload['status']} providers={list(payload['providers'].keys())}"


def chat_stream_check(r: CheckResult) -> None:
    events = _read_sse_events("/chat/stream", {"message": "Say hi in five words.", "context_type": "chat"})
    assert events, "no events received"
    types = {e.get("type") for e in events}
    assert "status" in types or "token" in types, f"unexpected event types: {types}"
    final_types = [e["type"] for e in events[-3:]]
    assert "done" in final_types or "error" in final_types, f"stream did not terminate: {final_types}"
    has_token = any(e.get("type") == "token" for e in events)
    r.detail = f"events={len(events)} got_tokens={has_token}"


def agents_run_check(r: CheckResult) -> None:
    events = _read_sse_events(
        "/agents/run",
        {"task": "What is 2+2?", "context_type": "chat", "engine": "graph"},
    )
    assert events, "no events received"
    nodes_seen = {e.get("node") for e in events if e.get("type") == "status"}
    assert "router" in nodes_seen, f"router not seen, nodes={nodes_seen}"
    r.detail = f"events={len(events)} nodes={sorted(n for n in nodes_seen if n)}"


def complete_check(r: CheckResult) -> None:
    status, body = _fetch(
        "POST",
        "/agents/complete",
        {"messages": [{"role": "user", "content": "Reply with the word OK."}], "cascade": "speed"},
    )
    assert status == 200, f"status={status}"
    payload = json.loads(body)
    data = payload.get("data") or {}
    assert data.get("content"), f"empty content: {data}"
    r.detail = f"provider={data.get('provider')} model={data.get('model')} latency_ms={data.get('latency_ms', 0):.0f}"


def main() -> int:
    print(f"AgentOS E2E smoke against {BACKEND_URL}\n")

    checks = [
        ("health", health_check),
        ("chat/stream", chat_stream_check),
        ("agents/run (graph)", agents_run_check),
        ("agents/complete", complete_check),
    ]

    results = []
    for name, fn in checks:
        result = check(name, fn)
        results.append(result)
        marker = "PASS" if result.ok else "FAIL"
        print(f"  [{marker}] {name:<25} {result.elapsed_ms:7.0f} ms  {result.detail}")

    total_pass = sum(1 for r in results if r.ok)
    print(f"\n{total_pass}/{len(results)} checks passed.")
    return 0 if total_pass == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
