from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass
class GeofenceBreachResult:
    inside: bool
    distance_from_center_meters: float | None = None
    geofence_name: str = "custom_geofence"


def point_in_circle(
    lat: float, lon: float, center_lat: float, center_lon: float, radius_meters: float
) -> GeofenceBreachResult:
    R = 6371000.0  # Earth radius in meters
    d_lat = math.radians(lat - center_lat)
    d_lon = math.radians(lon - center_lon)
    a = (
        math.sin(d_lat / 2.0) ** 2
        + math.cos(math.radians(center_lat))
        * math.cos(math.radians(lat))
        * math.sin(d_lon / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    distance = R * c

    return GeofenceBreachResult(
        inside=distance <= radius_meters,
        distance_from_center_meters=round(distance, 1),
    )


def point_in_polygon(lat: float, lon: float, polygon: list[tuple[float, float]]) -> bool:
    # Ray-casting algorithm for point-in-polygon test
    # polygon is a list of (lat, lon) coordinates
    n = len(polygon)
    inside = False

    if n < 3:
        return False

    p1_lat, p1_lon = polygon[0]
    for i in range(n + 1):
        p2_lat, p2_lon = polygon[i % n]
        if lon > min(p1_lon, p2_lon):
            if lon <= max(p1_lon, p2_lon):
                if lat <= max(p1_lat, p2_lat):
                    if p1_lon != p2_lon:
                        x_inters = (lon - p1_lon) * (p2_lat - p1_lat) / (p2_lon - p1_lon) + p1_lat
                    else:
                        x_inters = p1_lat
                    if p1_lat == p2_lat or lat <= x_inters:
                        inside = not inside
        p1_lat, p1_lon = p2_lat, p2_lon

    return inside
