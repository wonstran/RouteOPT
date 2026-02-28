from __future__ import annotations

from routeopt.core.solver import (
    NightRoute,
    build_engine,
    estimate_night_deadhead,
    estimate_night_hours,
    estimate_night_service,
)
from routeopt.models.constraints import Constraints
from routeopt.utils.geo import LatLon


def routes_to_json(constraints: Constraints, nights: list[NightRoute]) -> dict:
    depot = LatLon(lat=constraints.depot.lat, lon=constraints.depot.lon)
    all_blocks = [b for n in nights for b in n.blocks]
    engine = build_engine(constraints, depot, all_blocks)

    routes = []
    total_dead = 0.0
    total_service = 0.0

    for idx, night in enumerate(nights, start=1):
        dead = estimate_night_deadhead(engine, depot, night.blocks)
        svc = estimate_night_service(constraints, engine, night.blocks)
        dur_h = estimate_night_hours(constraints, engine, depot, night.blocks)

        total_dead += dead.distance_miles
        total_service += svc.distance_miles

        steps = []
        if night.blocks:
            # depot -> first
            leg = engine.dist_time(depot, night.blocks[0].start)
            steps.append(
                {
                    "type": "deadhead",
                    "from": "Depot",
                    "to": f"{night.blocks[0].roadway_id}:{night.blocks[0].direction}:start",
                    "distance_miles": round(leg.distance_miles, 4),
                    "duration_hours": round(leg.duration_hours, 4),
                }
            )

        for i, b in enumerate(night.blocks):
            steps.append(
                {
                    "type": "service_block",
                    "roadway_id": b.roadway_id,
                    "direction": b.direction,
                    "azimuth_deg": round(b.azimuth_deg, 2),
                    "passes_required": b.passes_required,
                    "service_distance_miles": round(b.service_distance_miles, 4),
                    "speed_limit_mph": b.speed_limit_mph,
                }
            )
            # between blocks
            if i + 1 < len(night.blocks):
                leg = engine.dist_time(b.end, night.blocks[i + 1].start)
                steps.append(
                    {
                        "type": "deadhead",
                        "from": f"{b.roadway_id}:{b.direction}:end",
                        "to": f"{night.blocks[i + 1].roadway_id}:{night.blocks[i + 1].direction}:start",
                        "distance_miles": round(leg.distance_miles, 4),
                        "duration_hours": round(leg.duration_hours, 4),
                    }
                )

        if night.blocks:
            leg = engine.dist_time(night.blocks[-1].end, depot)
            steps.append(
                {
                    "type": "deadhead",
                    "from": f"{night.blocks[-1].roadway_id}:{night.blocks[-1].direction}:end",
                    "to": "Depot",
                    "distance_miles": round(leg.distance_miles, 4),
                    "duration_hours": round(leg.duration_hours, 4),
                }
            )

        buffer_h = max(0.0, constraints.limits.max_hours_per_night - dur_h)

        routes.append(
            {
                "night_index": idx,
                "duration_hours": round(dur_h, 4),
                "deadhead_miles": round(dead.distance_miles, 4),
                "deadhead_hours": round(dead.duration_hours, 4),
                "service_miles": round(svc.distance_miles, 4),
                "service_hours": round(svc.duration_hours, 4),
                "buffer_hours": round(buffer_h, 4),
                "steps": steps,
            }
        )

    return {
        "meta": {
            "total_nights": len(nights),
            "total_deadhead_miles": round(total_dead, 4),
            "total_service_miles": round(total_service, 4),
            "constraints": {
                "max_hours_per_night": constraints.limits.max_hours_per_night,
                "max_nights": constraints.limits.max_nights,
                "routing_engine": constraints.routing_engine,
                "loopback_mode": constraints.loopback.mode,
            },
        },
        "routes": routes,
    }
