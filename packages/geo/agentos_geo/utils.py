import math

from .types import GeoPoint


def haversine_distance(a: GeoPoint, b: GeoPoint) -> float:
    R = 6371.0
    lat1, lat2 = math.radians(a.lat), math.radians(b.lat)
    dlat = math.radians(b.lat - a.lat)
    dlon = math.radians(b.lon - a.lon)
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return R * 2 * math.atan2(math.sqrt(h), math.sqrt(1 - h))


def to_geojson_point(point: GeoPoint) -> dict:
    return {
        "type": "Feature",
        "geometry": {"type": "Point", "coordinates": [point.lon, point.lat]},
        "properties": {"label": point.label},
    }


def to_geojson_collection(points: list[GeoPoint]) -> dict:
    return {
        "type": "FeatureCollection",
        "features": [to_geojson_point(p) for p in points],
    }
