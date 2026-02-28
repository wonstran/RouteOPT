from __future__ import annotations

import argparse
import json
from pathlib import Path

from routeopt.core.config import load_constraints
from routeopt.core.ingest import load_segments_geojson
from routeopt.core.output import routes_to_json
from routeopt.core.solver import greedy_plan
from routeopt.core.tasks import build_service_blocks


def main(argv=None):
    p = argparse.ArgumentParser(prog="routeopt")
    sub = p.add_subparsers(dest="cmd", required=True)

    plan = sub.add_parser("plan", help="Generate nightly measurement routes")
    plan.add_argument("--input", required=True, help="Input GeoJSON file")
    plan.add_argument("--constraints", required=True, help="Constraints YAML")
    plan.add_argument("--output", default="routes.json", help="Output routes JSON")

    args = p.parse_args(argv)

    if args.cmd == "plan":
        constraints = load_constraints(args.constraints)
        segments = load_segments_geojson(args.input, default_oneway=constraints.oneway.default)
        blocks = build_service_blocks(segments)
        nights = greedy_plan(constraints, blocks)
        out = routes_to_json(constraints, nights)
        Path(args.output).write_text(json.dumps(out, indent=2), encoding="utf-8")
        return
