from __future__ import annotations


from routeopt.core.solver import NightRoute, estimate_night_deadhead_miles, estimate_night_hours
from routeopt.models.constraints import Constraints
from routeopt.utils.geo import LatLon


def routes_to_json(constraints: Constraints, nights: list[NightRoute]) -> dict:
    depot = LatLon(lat=constraints.depot.lat, lon=constraints.depot.lon)

    routes = []
    total_dead = 0.0
    total_service = 0.0

    for idx, night in enumerate(nights, start=1):
        dead_mi = estimate_night_deadhead_miles(depot, night.blocks)
        dur_h = estimate_night_hours(constraints, depot, night.blocks)
        total_dead += dead_mi
        total_service += sum(b.service_distance_miles for b in night.blocks)

        steps = []
        # deadhead + service blocks; detailed leg polylines come later (OSM engine)
        if night.blocks:
            steps.append(
                {
                    "type": "deadhead",
                    "from": "Depot",
                    "to": f"{night.blocks[0].roadway_id}:{night.blocks[0].direction}:start",
                    "distance_miles": None,
                }
            )
        for b in night.blocks:
            steps.append(
                {
                    "type": "service_block",
                    "roadway_id": b.roadway_id,
                    "direction": b.direction,
                    "azimuth_deg": b.azimuth_deg,
                    "passes_required": b.passes_required,
                    "service_distance_miles": b.service_distance_miles,
                    "speed_limit_mph": b.speed_limit_mph,
                }
            )
        if night.blocks:
            steps.append(
                {
                    "type": "deadhead",
                    "from": f"{night.blocks[-1].roadway_id}:{night.blocks[-1].direction}:end",
                    "to": "Depot",
                    "distance_miles": None,
                }
            )

        routes.append(
            {
                "night_index": idx,
                "duration_hours": round(dur_h, 4),
                "deadhead_miles": round(dead_mi, 4),
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
            },
        },
        "routes": routes,
    }
