from __future__ import annotations

from dataclasses import dataclass, field

from routeopt.core.routing import DistTime, EuclideanRouting, OSMnxRouting, RoutingEngine
from routeopt.core.tasks import ServiceBlock
from routeopt.models.constraints import Constraints
from routeopt.utils.geo import LatLon


@dataclass
class Step:
    type: str  # deadhead|service_block
    payload: dict


@dataclass
class NightRoute:
    blocks: list[ServiceBlock] = field(default_factory=list)


def build_engine(constraints: Constraints, depot: LatLon, blocks: list[ServiceBlock]) -> RoutingEngine:
    mph = max(1e-6, constraints.speed.deadhead_speed_mph * constraints.speed.deadhead_factor)
    if constraints.routing_engine == "osmnx":
        pts: list[LatLon] = []
        for b in blocks:
            pts.append(b.start)
            pts.append(b.end)
        return OSMnxRouting(
            depot=depot,
            points=pts,
            buffer_miles=constraints.osm_buffer_miles,
            deadhead_speed_mph=mph,
        )
    return EuclideanRouting(deadhead_speed_mph=mph)


def service_speed_mph(constraints: Constraints, block: ServiceBlock) -> float:
    return max(1e-6, block.speed_limit_mph * min(1.0, constraints.speed.service_factor))


def deadhead_speed_mph(constraints: Constraints) -> float:
    return max(1e-6, constraints.speed.deadhead_speed_mph * constraints.speed.deadhead_factor)


def loopback_dist_time(
    constraints: Constraints, engine: RoutingEngine, block: ServiceBlock
) -> DistTime:
    """Distance/time to reposition for the next pass of the same service block.

    When loopback.mode=routing, compute shortest path from end->start.
    When constant, use constant_seconds and 0 distance.
    """

    extra_passes = max(0, block.passes_required - 1)
    if extra_passes == 0:
        return DistTime(distance_miles=0.0, duration_hours=0.0)

    if constraints.loopback.mode == "routing":
        one = engine.dist_time(block.end, block.start)
        return DistTime(
            distance_miles=one.distance_miles * extra_passes,
            duration_hours=one.duration_hours * extra_passes,
        )

    # constant
    sec = float(constraints.loopback.constant_seconds) * extra_passes
    return DistTime(distance_miles=0.0, duration_hours=sec / 3600.0)


def service_dist_time(constraints: Constraints, block: ServiceBlock) -> DistTime:
    mph = service_speed_mph(constraints, block)
    hours = block.service_distance_miles / mph
    return DistTime(distance_miles=block.service_distance_miles, duration_hours=hours)


def deadhead_leg(engine: RoutingEngine, a: LatLon, b: LatLon) -> DistTime:
    return engine.dist_time(a, b)


def estimate_night_deadhead(
    engine: RoutingEngine, depot: LatLon, blocks: list[ServiceBlock]
) -> DistTime:
    if not blocks:
        return DistTime(distance_miles=0.0, duration_hours=0.0)

    legs = [
        deadhead_leg(engine, depot, blocks[0].start),
        *(
            deadhead_leg(engine, a.end, b.start)
            for a, b in zip(blocks, blocks[1:])
        ),
        deadhead_leg(engine, blocks[-1].end, depot),
    ]
    return DistTime(
        distance_miles=sum(l.distance_miles for l in legs),
        duration_hours=sum(l.duration_hours for l in legs),
    )


def estimate_night_service(
    constraints: Constraints, engine: RoutingEngine, blocks: list[ServiceBlock]
) -> DistTime:
    dist = 0.0
    hours = 0.0
    for b in blocks:
        s = service_dist_time(constraints, b)
        lb = loopback_dist_time(constraints, engine, b)
        dist += s.distance_miles + lb.distance_miles
        hours += s.duration_hours + lb.duration_hours
    return DistTime(distance_miles=dist, duration_hours=hours)


def estimate_night_hours(
    constraints: Constraints, engine: RoutingEngine, depot: LatLon, blocks: list[ServiceBlock]
) -> float:
    dead = estimate_night_deadhead(engine, depot, blocks)
    svc = estimate_night_service(constraints, engine, blocks)
    return dead.duration_hours + svc.duration_hours


def greedy_plan(constraints: Constraints, blocks: list[ServiceBlock]) -> list[NightRoute]:
    depot = LatLon(lat=constraints.depot.lat, lon=constraints.depot.lon)
    max_h = constraints.limits.max_hours_per_night

    # Build one engine for the whole solve so we don't rebuild OSM graphs inside loops.
    engine = build_engine(constraints, depot, blocks)

    blocks_sorted = sorted(blocks, key=lambda b: service_dist_time(constraints, b).duration_hours, reverse=True)

    nights: list[NightRoute] = []

    for blk in blocks_sorted:
        best = None
        for ni, night in enumerate(nights):
            for pos in range(len(night.blocks) + 1):
                cand = night.blocks[:pos] + [blk] + night.blocks[pos:]
                h = estimate_night_hours(constraints, engine, depot, cand)
                if h > max_h:
                    continue
                dead = estimate_night_deadhead(engine, depot, cand)
                if best is None or dead.distance_miles < best[0]:
                    best = (dead.distance_miles, ni, pos)

        if best is not None:
            _, ni, pos = best
            nights[ni].blocks.insert(pos, blk)
            continue

        h_single = estimate_night_hours(constraints, engine, depot, [blk])
        if h_single > max_h:
            raise ValueError(
                f"Single service block cannot fit in a night (hours={h_single:.3f} > {max_h}). "
                "Consider splitting geometry or adjusting constraints."
            )

        if len(nights) + 1 > constraints.limits.max_nights:
            raise ValueError("Cannot schedule within max_nights constraint")
        nights.append(NightRoute(blocks=[blk]))

    return nights
