import os

import asyncpg

from .types import GeoPoint


async def _get_pool() -> asyncpg.Pool:
    return await asyncpg.create_pool(os.getenv("DATABASE_URL"))


async def find_within_radius(center: GeoPoint, radius_km: float, table: str = "locations") -> list[dict]:
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"""
            SELECT *, ST_Distance(
                geom::geography,
                ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography
            ) / 1000 AS distance_km
            FROM {table}
            WHERE ST_DWithin(
                geom::geography,
                ST_SetSRID(ST_MakePoint($1, $2), 4326)::geography,
                $3 * 1000
            )
            ORDER BY distance_km
            """,
            center.lon,
            center.lat,
            radius_km,
        )
        return [dict(row) for row in rows]


async def find_within_bbox(min_lat: float, min_lon: float, max_lat: float, max_lon: float, table: str = "locations") -> list[dict]:
    pool = await _get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"""
            SELECT * FROM {table}
            WHERE geom && ST_MakeEnvelope($1, $2, $3, $4, 4326)
            """,
            min_lon,
            min_lat,
            max_lon,
            max_lat,
        )
        return [dict(row) for row in rows]
