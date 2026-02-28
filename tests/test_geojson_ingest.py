import json
from pathlib import Path

import pytest

from routeopt.core.ingest import load_segments_geojson


def test_load_segments_geojson_minimal(tmp_path: Path):
    gj = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "roadway_id": "R1",
                    "total_lanes": 4,
                    "speed_limit": 40,
                    "oneway": False,
                },
                "geometry": {
                    "type": "LineString",
                    "coordinates": [[-82.4163460, 28.0585626], [-82.4163460, 28.0685626]],
                },
            }
        ],
    }
    p = tmp_path / "in.geojson"
    p.write_text(json.dumps(gj), encoding="utf-8")
    segs = load_segments_geojson(p, default_oneway=False)
    assert len(segs) == 1
    assert segs[0].roadway_id == "R1"


def test_load_segments_geojson_rejects_non_linestring(tmp_path: Path):
    gj = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"roadway_id": "R1", "total_lanes": 2, "speed_limit": 40},
                "geometry": {"type": "Point", "coordinates": [-82.4, 28.0]},
            }
        ],
    }
    p = tmp_path / "in.geojson"
    p.write_text(json.dumps(gj), encoding="utf-8")
    with pytest.raises(ValueError):
        load_segments_geojson(p, default_oneway=False)
