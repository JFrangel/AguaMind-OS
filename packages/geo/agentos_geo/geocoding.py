from geopy.geocoders import Nominatim
from geopy.adapters import AioHTTPAdapter

from .types import GeoPoint


async def geocode(address: str) -> GeoPoint | None:
    async with Nominatim(
        user_agent="agentos",
        adapter_factory=AioHTTPAdapter,
    ) as geolocator:
        location = await geolocator.geocode(address)
        if location:
            return GeoPoint(lat=location.latitude, lon=location.longitude, label=location.address)
        return None


async def reverse_geocode(lat: float, lon: float) -> str | None:
    async with Nominatim(
        user_agent="agentos",
        adapter_factory=AioHTTPAdapter,
    ) as geolocator:
        location = await geolocator.reverse(f"{lat}, {lon}")
        return location.address if location else None


async def batch_geocode(addresses: list[str]) -> list[GeoPoint | None]:
    results = []
    for address in addresses:
        point = await geocode(address)
        results.append(point)
    return results
