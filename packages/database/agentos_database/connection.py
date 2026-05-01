from __future__ import annotations

import os
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


class DatabaseConnection:
    """Async SQLAlchemy engine + dialect detection.

    Accepts any SQLAlchemy URL. Handles dialect normalization for the common
    cases (`postgres://` → `postgresql+asyncpg://`, etc.).
    """

    def __init__(self, url: str, *, pool_size: int = 5):
        self.url = _normalize_url(url)
        self.dialect = self.url.split("+")[0].split(":")[0]  # postgresql / mysql / sqlite
        # SQLite uses StaticPool which doesn't accept pool_size/pool_pre_ping.
        kwargs: dict = {"future": True}
        if self.dialect != "sqlite":
            kwargs["pool_size"] = pool_size
            kwargs["pool_pre_ping"] = True
        self.engine: AsyncEngine = create_async_engine(self.url, **kwargs)

    async def close(self) -> None:
        await self.engine.dispose()

    def __repr__(self) -> str:
        host = urlparse(self.url.replace("+asyncpg", "").replace("+aiomysql", "").replace("+aiosqlite", "")).hostname
        return f"DatabaseConnection(dialect={self.dialect}, host={host})"


def connect(url: str | None = None, *, pool_size: int = 5) -> DatabaseConnection:
    """Build a connection from `url` or `DATABASE_URL_USER` env var.

    The env var name avoids clashing with `DATABASE_URL` (used by Supabase
    for AgentOS internal tables). Use `DATABASE_URL_USER` for the user's
    business database that agents will query.
    """
    url = url or os.getenv("DATABASE_URL_USER") or os.getenv("DATABASE_URL", "")
    if not url:
        raise RuntimeError("DATABASE_URL_USER not set and no url passed")
    return DatabaseConnection(url, pool_size=pool_size)


def _normalize_url(url: str) -> str:
    """Normalize common URL prefixes to async drivers SQLAlchemy expects."""
    if url.startswith("postgres://"):
        url = "postgresql+asyncpg://" + url[len("postgres://") :]
    elif url.startswith("postgresql://") and "+" not in url[: url.index("://")]:
        url = "postgresql+asyncpg://" + url[len("postgresql://") :]
    elif url.startswith("mysql://"):
        url = "mysql+aiomysql://" + url[len("mysql://") :]
    elif url.startswith("sqlite://") and "+" not in url[: url.index("://")]:
        url = "sqlite+aiosqlite://" + url[len("sqlite://") :]
    return url
