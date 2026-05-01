"""Endpoints to query the user's connected business database.

Distinct from AgentOS's own Supabase: `DATABASE_URL_USER` points at the
user's data; the LLM can be asked questions in natural language and
generate SQL via /database/nl-query, or run SQL directly via /database/query.
"""
from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

router = APIRouter()

_connection = None
_introspector = None
_executor = None


def _get_components():
    """Lazy-init the DB components so the API can boot without DATABASE_URL_USER."""
    global _connection, _introspector, _executor
    if _connection is not None:
        return _connection, _introspector, _executor
    if not (os.getenv("DATABASE_URL_USER") or os.getenv("DATABASE_URL")):
        raise HTTPException(
            status_code=503,
            detail="DATABASE_URL_USER not configured",
        )
    from agentos_database import SafeQueryExecutor, SchemaIntrospector, connect

    _connection = connect()
    _introspector = SchemaIntrospector(_connection)
    _executor = SafeQueryExecutor(_connection, read_only=True, max_rows=500)
    return _connection, _introspector, _executor


class QueryRequest(BaseModel):
    sql: str
    params: dict | None = None


class NLQueryRequest(BaseModel):
    question: str
    cascade: str = "reasoning"
    max_tables_in_context: int = 30


@router.get("/schema")
async def schema():
    """Returns full schema as structured JSON."""
    _, introspector, _ = _get_components()
    tables = await introspector.all()
    return {
        "data": [
            {
                "name": t.name,
                "primary_keys": t.primary_keys,
                "columns": [
                    {
                        "name": c.name,
                        "type": c.type,
                        "nullable": c.nullable,
                        "primary_key": c.primary_key,
                    }
                    for c in t.columns
                ],
                "foreign_keys": t.foreign_keys,
            }
            for t in tables
        ],
        "error": None,
        "meta": {"table_count": len(tables)},
    }


@router.post("/query")
async def query(body: QueryRequest):
    """Execute a SQL SELECT against the connected DB. Read-only enforced."""
    from agentos_database import UnsafeQueryError

    _, _, executor = _get_components()
    try:
        result = await executor.execute(body.sql, body.params)
    except UnsafeQueryError as e:
        return JSONResponse(
            status_code=400,
            content={"data": None, "error": "unsafe_query", "meta": {"detail": str(e)}},
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"data": None, "error": "query_failed", "meta": {"detail": f"{type(e).__name__}: {e}"}},
        )

    return {
        "data": {"columns": result.columns, "rows": result.rows},
        "error": None,
        "meta": {"row_count": result.row_count, "elapsed_ms": result.elapsed_ms},
    }


@router.post("/nl-query")
async def nl_query(body: NLQueryRequest, request: Request):
    """Natural-language question → SQL via LLM → executed → returned with rows.

    Two-stage: (1) LLM generates SQL given the schema. (2) executor runs it
    in read-only mode. The generated SQL is returned alongside the results
    so the user can audit and tweak.
    """
    from agentos_database import UnsafeQueryError
    from agentos_llm.factory import AllProvidersFailedError

    _, introspector, executor = _get_components()
    schema_text = await introspector.schema_text(max_tables=body.max_tables_in_context)

    factory = request.app.state.llm_factory
    system = (
        "You translate natural-language questions into a single SQL SELECT query for the schema below.\n"
        "Rules:\n"
        "1. Output ONLY the SQL — no markdown, no explanation, no semicolons at the end.\n"
        "2. Use only SELECT (read-only). No INSERT/UPDATE/DELETE/DDL.\n"
        "3. If the question is unanswerable from the schema, output exactly: NO_QUERY\n"
        "4. Always include a LIMIT clause (max 200 rows).\n\n"
        f"Schema:\n{schema_text}"
    )
    try:
        completion = await factory.complete_with_fallback(
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": body.question},
            ],
            cascade=body.cascade,
            temperature=0.0,
            max_tokens=400,
        )
    except AllProvidersFailedError as e:
        return JSONResponse(
            status_code=503,
            content={"data": None, "error": "all_providers_failed", "meta": {"detail": str(e)}},
        )

    sql = _strip_sql(completion.content)
    if sql == "NO_QUERY" or not sql:
        return {
            "data": {"sql": None, "rows": [], "columns": [], "explanation": completion.content.strip()},
            "error": None,
            "meta": {"answered": False},
        }

    try:
        result = await executor.execute(sql)
    except UnsafeQueryError as e:
        return JSONResponse(
            status_code=400,
            content={
                "data": {"sql": sql, "rows": [], "columns": []},
                "error": "unsafe_query",
                "meta": {"detail": str(e)},
            },
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "data": {"sql": sql, "rows": [], "columns": []},
                "error": "query_failed",
                "meta": {"detail": f"{type(e).__name__}: {e}"},
            },
        )

    return {
        "data": {
            "sql": sql,
            "columns": result.columns,
            "rows": result.rows,
        },
        "error": None,
        "meta": {
            "row_count": result.row_count,
            "elapsed_ms": result.elapsed_ms,
            "provider": completion.provider.value,
            "model": completion.model,
        },
    }


def _strip_sql(text: str) -> str:
    """Strip markdown fences and trailing semicolons that LLMs love to add."""
    text = text.strip()
    if text.startswith("```"):
        # remove first line (```sql or ```) and last fence
        lines = text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        text = "\n".join(lines).strip()
    return text.rstrip(";").strip()
