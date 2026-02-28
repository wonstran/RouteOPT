from __future__ import annotations

from dataclasses import dataclass, field

from routeopt.core.tasks import ServiceBlock
from routeopt.models.constraints import Constraints
from routeopt.utils.geo import LatLon, haversine_miles


@dataclass
class Step:
    type: str  # deadhead|service_block
    payload: dict


@dataclass
class NightRoute:
    blocks: list[ServiceBlock] = field(default_factory=list)


def _deadhead_miles(a: LatLon, b: LatLon) -> float:
    return haversine_miles(a, b)


def _deadhead_hours(constraints: Constraints, miles: float) -> float:
    mph = max(1e-6, constraints.speed.deadhead_speed_mph * constraints.speed.deadhead_factor)
    return miles / mph


def _service_hours(constraints: Constraints, block: ServiceBlock) -> float:
    mph = max(1e-6, block.speed_limit_mph * min(1.0, constraints.speed.service_factor))
    return block.service_distance_miles / mph


def _loopback_hours(constraints: Constraints, block: ServiceBlock) -> float:
    # constant loopback per extra pass (routing mode not implemented in MVP)
    if block.passes_required <= 1:
        return 0.0
    if constraints.loopback.mode == "constant":
        return (block.passes_required - 1) * (constraints.loopback.constant_seconds / 3600.0)
    # routing mode placeholder: treat as constant until routing engine added
    return (block.passes_required - 1) * (constraints.loopback.constant_seconds / 3600.0)


def estimate_night_hours(constraints: Constraints, depot: LatLon, blocks: list[ServiceBlock]) -> float:
    if not blocks:
        return 0.0
    miles = 0.0
    # depot -> first
    miles += _deadhead_miles(depot, blocks[0].start)
    # between blocks
    for a, b in zip(blocks, blocks[1:]):
        miles += _deadhead_miles(a.end, b.start)
    # last -> depot
    miles += _deadhead_miles(blocks[-1].end, depot)

    deadhead_h = _deadhead_hours(constraints, miles)
    service_h = sum(_service_hours(constraints, b) + _loopback_hours(constraints, b) for b in blocks)
    return deadhead_h + service_h


def estimate_night_deadhead_miles(depot: LatLon, blocks: list[ServiceBlock]) -> float:
    if not blocks:
        return 0.0
    miles = _deadhead_miles(depot, blocks[0].start)
    for a, b in zip(blocks, blocks[1:]):
        miles += _deadhead_miles(a.end, b.start)
    miles += _deadhead_miles(blocks[-1].end, depot)
    return miles


def greedy_plan(constraints: Constraints, blocks: list[ServiceBlock]) -> list[NightRoute]:
    depot = LatLon(lat=constraints.depot.lat, lon=constraints.depot.lon)
    max_h = constraints.limits.max_hours_per_night

    # sort by service time descending as a simple difficulty heuristic
    blocks_sorted = sorted(blocks, key=lambda b: _service_hours(constraints, b), reverse=True)

    nights: list[NightRoute] = []

    for blk in blocks_sorted:
        best = None
        # try insert into existing nights at best position
        for ni, night in enumerate(nights):
            for pos in range(len(night.blocks) + 1):
                cand = night.blocks[:pos] + [blk] + night.blocks[pos:]
                h = estimate_night_hours(constraints, depot, cand)
                if h > max_h:
                    continue
                dead_mi = estimate_night_deadhead_miles(depot, cand)
                if best is None or dead_mi < best[0]:
                    best = (dead_mi, ni, pos)

        if best is not None:
            _, ni, pos = best
            nights[ni].blocks.insert(pos, blk)
            continue

        # else open new night, but only if the block itself is schedulable
        h_single = estimate_night_hours(constraints, depot, [blk])
        if h_single > max_h:
            raise ValueError(
                f"Single service block cannot fit in a night (hours={h_single:.3f} > {max_h}). "
                "Consider splitting geometry or adjusting constraints."
            )

        if len(nights) + 1 > constraints.limits.max_nights:
            raise ValueError("Cannot schedule within max_nights constraint")
        nights.append(NightRoute(blocks=[blk]))

    return nights
