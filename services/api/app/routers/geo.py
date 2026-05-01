from fastapi import APIRouter
from pydantic import BaseModel

from agentos_geo import geocoding
from agentos_geo.types import GeoPoint

router = APIRouter()


class GeocodeRequest(BaseModel):
    address: str


class RadiusSearchRequest(BaseModel):
    lat: float
    lon: float
    radius_km: float = 5.0


@router.post("/geocode")
async def geocode(body: GeocodeRequest):
    point = await geocoding.geocode(body.address)
    return {"data": point.model_dump() if point else None, "error": None}


@router.post("/reverse")
async def reverse(body: RadiusSearchRequest):
    address = await geocoding.reverse_geocode(body.lat, body.lon)
    return {"data": {"address": address}, "error": None}
