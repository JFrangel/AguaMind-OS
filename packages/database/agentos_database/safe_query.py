import re
from dataclasses import dataclass

from sqlalchemy import text

from .connection import DatabaseConnection


class UnsafeQueryError(Exception):
    """Raised when a query contains forbidden statements in read-only mode."""


@dataclass
class QueryResult:
    columns: list[str]
    rows: list[dict]
    row_count: int
    elapsed_ms: float


# Forbidden keywords in read-only mode. Match as whole words.
_FORBIDDEN = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|TRUNCATE|ALTER|CREATE|GRANT|REVOKE|RENAME|REPLACE|MERGE|CALL|EXEC|EXECUTE)\b",
    re.IGNORECASE,
)
_MULTI_STATEMENT = re.compile(r";\s*\S")


class SafeQueryExecutor:
    """Read-only query runner with allowlist enforcement.

    Defaults:
      * Read-only: blocks INSERT/UPDATE/DELETE/DDL/etc.
      * Single statement only (no `; DROP TABLE` shenanigans).
      * `LIMIT` injection if the query is a SELECT without one.
      * Result row cap to prevent OOM on huge tables.

    Pass `read_only=False` only when you trust the input fully (e.g.
    migration scripts run by an admin, not user-generated SQL).
    """

    def __init__(
        self,
        conn: DatabaseConnection,
        *,
        read_only: bool = True,
        max_rows: int = 500,
    ):
        self._conn = conn
        self._read_only = read_only
        self._max_rows = max_rows

    async def execute(
        self, sql: str, params: dict | None = None
    ) -> QueryResult:
        import time

        sql = sql.strip().rstrip(";")
        if not sql:
            raise UnsafeQueryError("empty query")

        if _MULTI_STATEMENT.search(sql + " "):
            raise UnsafeQueryError("multiple statements not allowed")

        if self._read_only:
            if not sql.lstrip().upper().startswith(("SELECT", "WITH")):
                raise UnsafeQueryError("read-only mode: only SELECT/WITH queries allowed")
            if _FORBIDDEN.search(sql):
                raise UnsafeQueryError("read-only mode: forbidden keyword detected")

        sql = self._inject_limit(sql)

        start = time.monotonic()
        # Use begin() so INSERT/UPDATE/DELETE auto-commit when read_only=False.
        async with self._conn.engine.begin() as connection:
            result = await connection.execute(text(sql), params or {})
            if result.returns_rows:
                mappings = list(result.mappings())[: self._max_rows]
                columns = list(mappings[0].keys()) if mappings else list(result.keys())
                rows = [dict(m) for m in mappings]
                row_count = len(rows)
            else:
                columns = []
                rows = []
                row_count = result.rowcount or 0
        elapsed_ms = (time.monotonic() - start) * 1000

        return QueryResult(
            columns=columns,
            rows=rows,
            row_count=row_count,
            elapsed_ms=elapsed_ms,
        )

    def _inject_limit(self, sql: str) -> str:
        upper = sql.lstrip().upper()
        # Only auto-LIMIT bare SELECT. WITH ... SELECT may have a LIMIT in
        # the CTE; appending to INSERT/UPDATE would syntax-error.
        if not upper.startswith("SELECT"):
            return sql
        if "LIMIT" in upper:
            return sql
        return f"{sql} LIMIT {self._max_rows}"
