import json
import os

import asyncpg

from .base import BaseVectorStore, SearchResult


class PgVectorStore(BaseVectorStore):
    """pgvector-backed store with proper format handling.

    The embedding column is `vector(384)` (matches SBERT all-MiniLM-L6-v2).
    pgvector accepts the literal `[v1,v2,...]` string format on insert and
    on the `<=>` distance operator. We pass embeddings as that string and
    cast to `vector` on the SQL side.
    """

    def __init__(self):
        self._pool: asyncpg.Pool | None = None

    async def _get_pool(self) -> asyncpg.Pool:
        if self._pool is None:
            dsn = os.getenv("DATABASE_URL")
            if not dsn:
                raise RuntimeError("DATABASE_URL not set; cannot use pgvector backend")
            self._pool = await asyncpg.create_pool(dsn)
        return self._pool

    async def upsert(self, documents: list[dict], embeddings: list[list[float]]) -> None:
        if not documents:
            return
        pool = await self._get_pool()
        rows = [
            (
                doc["id"],
                doc["content"],
                json.dumps(doc.get("metadata", {})),
                _to_pgvector(emb),
            )
            for doc, emb in zip(documents, embeddings)
        ]
        async with pool.acquire() as conn:
            await conn.executemany(
                """
                INSERT INTO documents (id, content, metadata, embedding)
                VALUES ($1, $2, $3::jsonb, $4::vector)
                ON CONFLICT (id) DO UPDATE
                SET content = EXCLUDED.content,
                    metadata = EXCLUDED.metadata,
                    embedding = EXCLUDED.embedding
                """,
                rows,
            )

    async def search(
        self, query_embedding: list[float], top_k: int = 5, filters: dict | None = None
    ) -> list[SearchResult]:
        pool = await self._get_pool()
        vector_literal = _to_pgvector(query_embedding)

        # Build filter clause with positional params. Single-value comparisons
        # use `metadata->>'key' = $N`, list values use `metadata->>'key' = ANY($N)`.
        where_clauses: list[str] = []
        params: list = [vector_literal, top_k]
        if filters:
            for key, value in filters.items():
                if isinstance(value, list):
                    params.append([str(v) for v in value])
                    where_clauses.append(f"metadata->>'{_escape_key(key)}' = ANY(${len(params)})")
                else:
                    params.append(str(value))
                    where_clauses.append(f"metadata->>'{_escape_key(key)}' = ${len(params)}")

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        sql = f"""
            SELECT id, content, metadata, 1 - (embedding <=> $1::vector) AS score
            FROM documents
            {where_sql}
            ORDER BY embedding <=> $1::vector
            LIMIT $2
        """
        async with pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)

        return [
            SearchResult(
                content=row["content"],
                metadata=_parse_jsonb(row["metadata"]),
                score=float(row["score"]),
                document_id=str(row["id"]),
            )
            for row in rows
        ]

    async def delete(self, document_ids: list[str]) -> None:
        if not document_ids:
            return
        pool = await self._get_pool()
        async with pool.acquire() as conn:
            await conn.execute("DELETE FROM documents WHERE id = ANY($1::uuid[])", document_ids)


def _to_pgvector(embedding: list[float]) -> str:
    """pgvector text format: '[v1,v2,...]'. No spaces, brackets required."""
    return "[" + ",".join(repr(float(v)) for v in embedding) + "]"


def _escape_key(key: str) -> str:
    """Block SQL injection in metadata key names. Keys are usually app-controlled
    constants but we sanitize anyway since they're interpolated into SQL.
    """
    if not key.replace("_", "").replace("-", "").isalnum():
        raise ValueError(f"invalid metadata key: {key!r}")
    return key.replace("'", "''")


def _parse_jsonb(value) -> dict:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return {}
    return {}
