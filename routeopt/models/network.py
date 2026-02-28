from __future__ import annotations

from dataclasses import dataclass

from routeopt.utils.geo import LatLon


@dataclass(frozen=True)
class Segment:
    roadway_id: str
    bmp: float | None
    emp: float | None
    total_lanes: int
    speed_limit_mph: float
    oneway: bool
    coords: list[LatLon]  # ordered geometry

    @property
    def start(self) -> LatLon:
        return self.coords[0]

    @property
    def end(self) -> LatLon:
        return self.coords[-1]
