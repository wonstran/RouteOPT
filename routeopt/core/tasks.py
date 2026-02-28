from __future__ import annotations

import math
from dataclasses import dataclass

from routeopt.models.network import Segment
from routeopt.utils.geo import LatLon, bearing_deg, haversine_miles


@dataclass(frozen=True)
class ServiceBlock:
    roadway_id: str
    direction: str  # 'A' or 'B'
    azimuth_deg: float
    passes_required: int
    speed_limit_mph: float
    start: LatLon
    end: LatLon
    service_distance_miles: float


def linestring_length_miles(coords: list[LatLon]) -> float:
    dist = 0.0
    for a, b in zip(coords, coords[1:]):
        dist += haversine_miles(a, b)
    return dist


def split_lanes_balanced(total_lanes: int) -> tuple[int, int]:
    a = int(math.ceil(total_lanes / 2))
    b = int(math.floor(total_lanes / 2))
    return a, b


def build_service_blocks(segments: list[Segment]) -> list[ServiceBlock]:
    blocks: list[ServiceBlock] = []
    for s in segments:
        seg_len = linestring_length_miles(s.coords)
        az = bearing_deg(s.start, s.end)

        if s.oneway:
            blocks.append(
                ServiceBlock(
                    roadway_id=s.roadway_id,
                    direction="A",
                    azimuth_deg=az,
                    passes_required=s.total_lanes,
                    speed_limit_mph=s.speed_limit_mph,
                    start=s.start,
                    end=s.end,
                    service_distance_miles=seg_len * s.total_lanes,
                )
            )
            continue

        lanes_a, lanes_b = split_lanes_balanced(s.total_lanes)
        blocks.append(
            ServiceBlock(
                roadway_id=s.roadway_id,
                direction="A",
                azimuth_deg=az,
                passes_required=lanes_a,
                speed_limit_mph=s.speed_limit_mph,
                start=s.start,
                end=s.end,
                service_distance_miles=seg_len * lanes_a,
            )
        )
        blocks.append(
            ServiceBlock(
                roadway_id=s.roadway_id,
                direction="B",
                azimuth_deg=(az + 180.0) % 360.0,
                passes_required=lanes_b,
                speed_limit_mph=s.speed_limit_mph,
                start=s.end,
                end=s.start,
                service_distance_miles=seg_len * lanes_b,
            )
        )
    # drop any zero-pass blocks (e.g., total_lanes=1 => B gets 0)
    return [b for b in blocks if b.passes_required > 0]
