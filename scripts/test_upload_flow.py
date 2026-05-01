"""Verify end-to-end that file upload + chat with RAG actually works,
not just the UI. This script:

  1. Boots the FastAPI app in-process (no uvicorn needed)
  2. Uploads a tiny synthetic doc to /rag/ingest
  3. Calls /rag/search to confirm the chunks landed
  4. Calls /chat/stream with use_rag=true to confirm the agent picks
     them up in the researcher node.

Run: python scripts/test_upload_flow.py
"""
from __future__ import annotations

import asyncio
import io
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "services" / "api"))

import httpx  # noqa: E402

from app.main import app  # noqa: E402


SYNTHETIC_DOC = """\
AgentOS internal note — Q2 roadmap

Las prioridades de Q2 2026 son:
- Lanzar el universal file adapter (PDF, DOCX, XLSX, JSON, CSV, MD, HTML)
- Integrar Tavily como segundo backend de búsqueda web
- Soporte multi-tenant en RAG con metadata_defaults

El responsable es Jose Frangel y el deadline interno es 2026-06-30.
"""


async def main() -> None:
    async with app.router.lifespan_context(app):
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            print("\n[1/4] HEALTH")
            r = await client.get("/health")
            data = r.json()
            providers = ", ".join(
                f"{n}={'up' if v.get('available') else 'down'}"
                for n, v in (data.get("providers") or {}).items()
            )
            print(f"     status={data['status']} {providers}")

            print("\n[2/4] UPLOAD synthetic note via /rag/ingest")
            files = {
                "file": ("q2-roadmap.md", io.BytesIO(SYNTHETIC_DOC.encode()), "text/markdown")
            }
            r = await client.post("/rag/ingest", files=files)
            up = r.json()
            print(f"     status={r.status_code} chunks_created={up['data']['chunks_created']}")
            print(f"     adapter={up['data'].get('adapter')}")

            print("\n[3/4] DIRECT search /rag/search")
            r = await client.post("/rag/search", json={"query": "Q2 deadline", "top_k": 3})
            s = r.json()
            print(f"     hits={s['meta']['count']}")
            for i, hit in enumerate(s["data"], 1):
                snippet = hit["content"].replace("\n", " ")[:120]
                print(f"     #{i} score={hit['score']:.3f}  {snippet}")

            print("\n[4/4] CHAT with use_rag=true — does the researcher actually use it?")
            payload = {
                "message": "¿Cuál es el deadline interno del Q2 roadmap y quién es el responsable?",
                "context_type": "research",
                "language": "es",
                "use_rag": True,
                "use_web": False,
            }
            seen_nodes: list[str] = []
            rag_status: list[str] = []
            tokens: list[str] = []
            async with client.stream(
                "POST", "/chat/stream", json=payload, timeout=60.0
            ) as resp:
                async for line in resp.aiter_lines():
                    if not line.startswith("data:"):
                        continue
                    try:
                        ev = json.loads(line[5:].strip())
                    except json.JSONDecodeError:
                        continue
                    t = ev.get("type")
                    if t == "status":
                        node = ev.get("node", "?")
                        seen_nodes.append(node)
                        if node == "rag":
                            rag_status.append(ev.get("content", ""))
                    elif t == "token":
                        tokens.append(ev.get("content", ""))
                    elif t == "error":
                        print(f"     ERROR event: {ev.get('error')}")
                    elif t == "done":
                        break

            answer = "".join(tokens)
            print(f"     nodes seen: {' -> '.join(dict.fromkeys(seen_nodes))}")
            print(f"     rag status: {rag_status}")
            print(f"     answer first 250 chars:")
            print("     " + answer[:250].replace("\n", "\n     "))

            print("\n[VERDICT]")
            mentions_jose = "Frangel" in answer or "Jose" in answer
            mentions_date = "2026-06-30" in answer or "junio" in answer.lower()
            rag_was_invoked = "rag" in seen_nodes
            print(f"   RAG node fired in pipeline: {rag_was_invoked}")
            print(f"   answer mentions Jose Frangel: {mentions_jose}")
            print(f"   answer mentions deadline date: {mentions_date}")
            ok = rag_was_invoked and (mentions_jose or mentions_date)
            print(f"   verdict: {'PASS — upload IS functional end-to-end' if ok else 'FAIL — upload not feeding the agent'}")


if __name__ == "__main__":
    asyncio.run(main())
