import pytest

from routeopt.core.solver import greedy_plan
from routeopt.core.tasks import ServiceBlock
from routeopt.models.constraints import Constraints
from routeopt.utils.geo import LatLon


def test_solver_rejects_single_block_over_limit():
    c = Constraints.model_validate(
        {
            "depot": {"lat": 0.0, "lon": 0.0},
            "limits": {"max_hours_per_night": 1.0, "max_nights": 200},
            "speed": {"service_factor": 1.0, "deadhead_factor": 1.0, "deadhead_speed_mph": 45.0},
            "loopback": {"mode": "constant", "constant_seconds": 0},
            "routing_engine": "euclidean",
        }
    )
    blk = ServiceBlock(
        roadway_id="R1",
        direction="A",
        azimuth_deg=0.0,
        passes_required=1,
        speed_limit_mph=10.0,
        start=LatLon(0.0, 0.0),
        end=LatLon(0.0, 0.0),
        service_distance_miles=20.0,
    )
    with pytest.raises(ValueError):
        greedy_plan(c, [blk])
