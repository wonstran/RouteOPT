from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from routeopt.utils.geo import LatLon, haversine_miles


@dataclass(frozen=True)
class DistTime:
    distance_miles: float
    duration_hours: float


class RoutingEngine(Protocol):
    def dist_time(self, a: LatLon, b: LatLon) -> DistTime: ...


@dataclass
class EuclideanRouting:
    deadhead_speed_mph: float

    def dist_time(self, a: LatLon, b: LatLon) -> DistTime:
        mi = haversine_miles(a, b)
        h = mi / max(1e-6, self.deadhead_speed_mph)
        return DistTime(distance_miles=mi, duration_hours=h)


class OSMnxRouting:
    """Skeleton for future: compute shortest paths on OSM drive network.

    Note: we keep this optional to avoid heavy deps for the core MVP.
    """

    def __init__(self):
        raise NotImplementedError("OSMnx routing engine not implemented yet")

    def dist_time(self, a: LatLon, b: LatLon) -> DistTime:
        raise NotImplementedError
