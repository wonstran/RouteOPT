from __future__ import annotations

import json
from pathlib import Path

from routeopt.models.network import Segment
from routeopt.utils.geo import LatLon


def _get(props: dict, *keys, default=None):
    for k in keys:
        if k in props and props[k] is not None:
            return props[k]
    return default


def _coerce_bool(value, *, default: bool) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        if value in (0, 0.0):
            return False
        if value in (1, 1.0):
            return True
        raise ValueError(f"Invalid boolean numeric: {value}")
    if isinstance(value, str):
        s = value.strip().lower()
        if s in ("true", "t", "yes", "y", "1"):
            return True
        if s in ("false", "f", "no", "n", "0", ""):
            return False
        raise ValueError(f"Invalid boolean string: {value}")
    raise ValueError(f"Invalid boolean type: {type(value)}")


def load_segments_geojson(path: str | Path, *, default_oneway: bool) -> list[Segment]:
    p = Path(path)
    data = json.loads(p.read_text(encoding="utf-8"))
    if data.get("type") != "FeatureCollection":
        raise ValueError("GeoJSON must be a FeatureCollection")

    segs: list[Segment] = []
    for feat in data.get("features", []):
        if feat.get("type") != "Feature":
            continue
        props = feat.get("properties") or {}
        geom = feat.get("geometry") or {}

        roadway_id = _get(props, "roadway_id", "roadway id", "id")
        if not roadway_id:
            raise ValueError("Missing roadway_id in feature properties")

        total_lanes = int(_get(props, "total_lanes", "number_of_lanes", "lanes", default=0))
        if total_lanes <= 0:
            raise ValueError(f"Invalid total_lanes for roadway_id={roadway_id}: {total_lanes}")

        speed_limit = float(_get(props, "speed_limit", "speed", "speedlimit", default=0))
        if speed_limit <= 0:
            raise ValueError(f"Invalid speed_limit for roadway_id={roadway_id}: {speed_limit}")

        oneway_raw = _get(props, "oneway", default=None)
        oneway = _coerce_bool(oneway_raw, default=default_oneway)
        bmp = _get(props, "bmp")
        emp = _get(props, "emp")

        if geom.get("type") != "LineString":
            raise ValueError(f"Only LineString supported (roadway_id={roadway_id})")
        coords_raw = geom.get("coordinates")
        if not coords_raw or len(coords_raw) < 2:
            raise ValueError(f"LineString must have >=2 coordinates (roadway_id={roadway_id})")

        coords: list[LatLon] = []
        for c in coords_raw:
            if not isinstance(c, (list, tuple)) or len(c) < 2:
                raise ValueError(f"Invalid coordinate in LineString (roadway_id={roadway_id}): {c}")
            lon, lat = c[0], c[1]
            coords.append(LatLon(lat=float(lat), lon=float(lon)))

        segs.append(
            Segment(
                roadway_id=str(roadway_id),
                bmp=float(bmp) if bmp is not None else None,
                emp=float(emp) if emp is not None else None,
                total_lanes=total_lanes,
                speed_limit_mph=speed_limit,
                oneway=oneway,
                coords=coords,
            )
        )

    if not segs:
        raise ValueError("GeoJSON contains no usable LineString features")
    return segs
