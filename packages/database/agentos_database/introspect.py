from dataclasses import dataclass, field

from sqlalchemy import inspect

from .connection import DatabaseConnection


@dataclass
class ColumnSchema:
    name: str
    type: str
    nullable: bool
    primary_key: bool = False


@dataclass
class TableSchema:
    name: str
    columns: list[ColumnSchema] = field(default_factory=list)
    primary_keys: list[str] = field(default_factory=list)
    foreign_keys: list[dict] = field(default_factory=list)
    row_count: int | None = None


class SchemaIntrospector:
    """Lists tables, columns, and FKs across all supported dialects.

    Used to feed a NL→SQL agent the schema as context, and to expose a
    structured `/database/schema` endpoint to the frontend.
    """

    def __init__(self, conn: DatabaseConnection):
        self._conn = conn

    async def list_tables(self) -> list[str]:
        async with self._conn.engine.connect() as connection:
            return await connection.run_sync(
                lambda sync_conn: inspect(sync_conn).get_table_names()
            )

    async def describe(self, table: str, *, include_row_count: bool = False) -> TableSchema:
        async with self._conn.engine.connect() as connection:
            schema = await connection.run_sync(lambda sc: _describe_sync(sc, table))
            if include_row_count:
                from sqlalchemy import text

                row = await connection.execute(text(f"SELECT COUNT(*) FROM {_quote(table)}"))
                count = row.scalar()
                schema.row_count = int(count) if count is not None else None
            return schema

    async def all(self, *, include_row_counts: bool = False) -> list[TableSchema]:
        names = await self.list_tables()
        return [await self.describe(n, include_row_count=include_row_counts) for n in names]

    async def schema_text(self, *, max_tables: int = 30) -> str:
        """Compact text representation suitable for an LLM prompt.

        Format:
            table users:
              - id (integer, PK, NOT NULL)
              - email (varchar, NOT NULL)
            table orders:
              - id (integer, PK)
              - user_id (integer, FK→users.id)
        """
        tables = await self.all()
        lines: list[str] = []
        for t in tables[:max_tables]:
            lines.append(f"table {t.name}:")
            for c in t.columns:
                marks = []
                if c.primary_key:
                    marks.append("PK")
                if not c.nullable:
                    marks.append("NOT NULL")
                fk = next((f for f in t.foreign_keys if f["from"] == c.name), None)
                if fk:
                    marks.append(f"FK→{fk['to_table']}.{fk['to_column']}")
                suffix = f" ({c.type}" + (", " + ", ".join(marks) if marks else "") + ")"
                lines.append(f"  - {c.name}{suffix}")
        return "\n".join(lines)


def _describe_sync(sync_conn, table: str) -> TableSchema:
    insp = inspect(sync_conn)
    columns_raw = insp.get_columns(table)
    pk_raw = insp.get_pk_constraint(table)
    fks_raw = insp.get_foreign_keys(table)

    pk_cols = pk_raw.get("constrained_columns", []) or []
    columns = [
        ColumnSchema(
            name=col["name"],
            type=str(col["type"]),
            nullable=bool(col.get("nullable", True)),
            primary_key=col["name"] in pk_cols,
        )
        for col in columns_raw
    ]
    foreign_keys = [
        {
            "from": fk["constrained_columns"][0] if fk["constrained_columns"] else None,
            "to_table": fk.get("referred_table"),
            "to_column": fk["referred_columns"][0] if fk.get("referred_columns") else None,
        }
        for fk in fks_raw
    ]
    return TableSchema(
        name=table,
        columns=columns,
        primary_keys=pk_cols,
        foreign_keys=foreign_keys,
    )


def _quote(name: str) -> str:
    """Block identifier injection. Allows alphanumeric + underscore + dot (for schema.table)."""
    if not all(c.isalnum() or c in ("_", ".") for c in name):
        raise ValueError(f"invalid table identifier: {name!r}")
    return name
