import json
from pathlib import Path

import pytest

from routeopt.core.ingest import load_segments_geojson


def _write(tmp_path: Path, oneway_value):
    gj = {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {
                    "roadway_id": "R1",
                    "total_lanes": 2,
                    "speed_limit": 30,
                    "oneway": oneway_value,
                },
                "geometry": {"type": "LineString", "coordinates": [[0, 0], [0, 1]]},
            }
        ],
    }
    p = tmp_path / "in.geojson"
    p.write_text(json.dumps(gj), encoding="utf-8")
    return p


def test_oneway_string_false(tmp_path: Path):
    p = _write(tmp_path, "false")
    seg = load_segments_geojson(p, default_oneway=True)[0]
    assert seg.oneway is False


def test_oneway_string_true(tmp_path: Path):
    p = _write(tmp_path, "true")
    seg = load_segments_geojson(p, default_oneway=False)[0]
    assert seg.oneway is True


def test_oneway_numeric_0(tmp_path: Path):
    p = _write(tmp_path, 0)
    seg = load_segments_geojson(p, default_oneway=True)[0]
    assert seg.oneway is False


def test_oneway_invalid_string(tmp_path: Path):
    p = _write(tmp_path, "maybe")
    with pytest.raises(ValueError):
        load_segments_geojson(p, default_oneway=False)
