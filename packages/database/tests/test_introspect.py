import pytest

aiosqlite = pytest.importorskip("aiosqlite")

from agentos_database import SchemaIntrospector, connect


@pytest.fixture
async def conn():
    c = connect("sqlite+aiosqlite:///:memory:")
    from sqlalchemy import text

    async with c.engine.begin() as conn:
        await conn.execute(
            text(
                "CREATE TABLE users ("
                "id INTEGER PRIMARY KEY, "
                "email TEXT NOT NULL, "
                "age INTEGER"
                ")"
            )
        )
        await conn.execute(
            text(
                "CREATE TABLE orders ("
                "id INTEGER PRIMARY KEY, "
                "user_id INTEGER NOT NULL REFERENCES users(id), "
                "total REAL"
                ")"
            )
        )
    yield c
    await c.close()


@pytest.mark.asyncio
async def test_list_tables(conn):
    introspector = SchemaIntrospector(conn)
    tables = await introspector.list_tables()
    assert sorted(tables) == ["orders", "users"]


@pytest.mark.asyncio
async def test_describe_picks_up_pk_and_nullability(conn):
    introspector = SchemaIntrospector(conn)
    schema = await introspector.describe("users")
    assert schema.name == "users"
    assert schema.primary_keys == ["id"]
    cols = {c.name: c for c in schema.columns}
    assert cols["email"].nullable is False
    assert cols["age"].nullable is True
    assert cols["id"].primary_key is True


@pytest.mark.asyncio
async def test_describe_picks_up_foreign_keys(conn):
    introspector = SchemaIntrospector(conn)
    schema = await introspector.describe("orders")
    fk_targets = [(fk["from"], fk["to_table"]) for fk in schema.foreign_keys]
    assert ("user_id", "users") in fk_targets


@pytest.mark.asyncio
async def test_schema_text_compact_for_llm(conn):
    introspector = SchemaIntrospector(conn)
    text = await introspector.schema_text()
    assert "table users:" in text
    assert "table orders:" in text
    assert "PK" in text
    assert "FK→users.id" in text
