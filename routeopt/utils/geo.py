from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class LatLon:
    lat: float
    lon: float


def haversine_miles(a: LatLon, b: LatLon) -> float:
    # Earth radius in miles
    r = 3958.7613
    lat1 = math.radians(a.lat)
    lat2 = math.radians(b.lat)
    dlat = lat2 - lat1
    dlon = math.radians(b.lon - a.lon)
    h = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def bearing_deg(a: LatLon, b: LatLon) -> float:
    # initial bearing from a->b (0=N, 90=E)
    lat1 = math.radians(a.lat)
    lat2 = math.radians(b.lat)
    dlon = math.radians(b.lon - a.lon)
    y = math.sin(dlon) * math.cos(lat2)
    x = math.cos(lat1) * math.sin(lat2) - math.sin(lat1) * math.cos(lat2) * math.cos(dlon)
    brng = math.degrees(math.atan2(y, x))
    return (brng + 360.0) % 360.0
