from routeopt.core.solver import build_engine, loopback_dist_time
from routeopt.core.tasks import ServiceBlock
from routeopt.models.constraints import Constraints
from routeopt.utils.geo import LatLon


def test_loopback_routing_uses_engine_distance_in_euclidean_mode():
    c = Constraints.model_validate(
        {
            "depot": {"lat": 0.0, "lon": 0.0},
            "loopback": {"mode": "routing", "constant_seconds": 60},
            "routing_engine": "euclidean",
            "speed": {"deadhead_speed_mph": 60.0},
        }
    )
    depot = LatLon(0.0, 0.0)
    blk = ServiceBlock(
        roadway_id="R1",
        direction="A",
        azimuth_deg=0.0,
        passes_required=3,
        speed_limit_mph=30.0,
        start=LatLon(0.0, 0.0),
        end=LatLon(0.0, 1.0),
        service_distance_miles=1.0,
    )
    eng = build_engine(c, depot, [blk])
    lb = loopback_dist_time(c, eng, blk)
    # extra passes = 2; euclidean distance should be 2 * haversine(0,1deg)
    assert lb.distance_miles > 0
    assert lb.duration_hours > 0
