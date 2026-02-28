from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field


class Depot(BaseModel):
    name: str = "Depot"
    lat: float
    lon: float


class Limits(BaseModel):
    max_hours_per_night: float = 4.0
    max_nights: int = 200


class Speed(BaseModel):
    service_factor: float = 1.0
    deadhead_factor: float = 1.0
    deadhead_speed_mph: float = 45.0


class LaneSplit(BaseModel):
    strategy: Literal["balanced"] = "balanced"


class Oneway(BaseModel):
    default: bool = False


class Loopback(BaseModel):
    mode: Literal["constant", "routing"] = "constant"
    constant_seconds: float = 60.0


class Objective(BaseModel):
    primary: Literal["min_deadhead_distance"] = "min_deadhead_distance"
    secondary: Literal["min_deadhead_time"] = "min_deadhead_time"


class Constraints(BaseModel):
    depot: Depot
    limits: Limits = Field(default_factory=Limits)
    speed: Speed = Field(default_factory=Speed)
    lane_split: LaneSplit = Field(default_factory=LaneSplit)
    oneway: Oneway = Field(default_factory=Oneway)
    loopback: Loopback = Field(default_factory=Loopback)
    objective: Objective = Field(default_factory=Objective)

    # Optional: bounding box buffer for future OSM graph build
    osm_buffer_miles: float = 2.0

    # Reserved for future routing engines
    routing_engine: Literal["euclidean", "osmnx"] = "euclidean"
