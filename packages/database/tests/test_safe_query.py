"""SafeQueryExecutor tests using SQLite in-memory.

Avoids spinning up Postgres while still exercising the real SQL parsing
path through SQLAlchemy.
"""
import pytest

aiosqlite = pytest.importorskip("aiosqlite")

from agentos_database import SafeQueryExecutor, UnsafeQueryError, connect


@pytest.fixture
async def conn():
    c = connect("sqlite+aiosqlite:///:memory:")
    from sqlalchemy import text

    async with c.engine.begin() as conn:
        await conn.execute(text("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT)"))
        await conn.execute(text("INSERT INTO users (name) VALUES ('alice'), ('bob'), ('carol')"))
    yield c
    await c.close()


@pytest.mark.asyncio
async def test_select_returns_rows(conn):
    executor = SafeQueryExecutor(conn)
    result = await executor.execute("SELECT id, name FROM users ORDER BY id")
    assert result.row_count == 3
    assert result.columns == ["id", "name"]
    assert result.rows[0]["name"] == "alice"


@pytest.mark.asyncio
async def test_blocks_insert(conn):
    executor = SafeQueryExecutor(conn)
    with pytest.raises(UnsafeQueryError):
        await executor.execute("INSERT INTO users (name) VALUES ('eve')")


@pytest.mark.asyncio
async def test_blocks_drop(conn):
    executor = SafeQueryExecutor(conn)
    with pytest.raises(UnsafeQueryError):
        await executor.execute("DROP TABLE users")


@pytest.mark.asyncio
async def test_blocks_multi_statement(conn):
    executor = SafeQueryExecutor(conn)
    with pytest.raises(UnsafeQueryError):
        await executor.execute("SELECT * FROM users; DROP TABLE users")


@pytest.mark.asyncio
async def test_blocks_select_with_hidden_update(conn):
    """Catches injection attempts via comments or weird whitespace."""
    executor = SafeQueryExecutor(conn)
    with pytest.raises(UnsafeQueryError):
        await executor.execute("SELECT * FROM users WHERE 1=1 UPDATE users SET name='x'")


@pytest.mark.asyncio
async def test_max_rows_caps_results(conn):
    executor = SafeQueryExecutor(conn, max_rows=2)
    result = await executor.execute("SELECT * FROM users")
    assert result.row_count == 2


@pytest.mark.asyncio
async def test_with_clause_allowed(conn):
    executor = SafeQueryExecutor(conn)
    result = await executor.execute(
        "WITH t AS (SELECT * FROM users) SELECT count(*) AS n FROM t"
    )
    assert result.rows[0]["n"] == 3


@pytest.mark.asyncio
async def test_read_only_off_allows_insert(conn):
    """Trusted-mode escape hatch must still work when explicitly enabled."""
    executor = SafeQueryExecutor(conn, read_only=False)
    # No exception — inserts into the in-memory test DB.
    await executor.execute("INSERT INTO users (name) VALUES ('eve')")
