import argparse
import json
from pathlib import Path

import yaml


def main(argv=None):
    p = argparse.ArgumentParser(prog="routeopt")
    sub = p.add_subparsers(dest="cmd", required=True)

    plan = sub.add_parser("plan", help="Generate nightly measurement routes")
    plan.add_argument("--input", required=True, help="Input GeoJSON file")
    plan.add_argument("--constraints", required=True, help="Constraints YAML")
    plan.add_argument("--output", default="routes.json", help="Output routes JSON")

    args = p.parse_args(argv)

    if args.cmd == "plan":
        constraints = yaml.safe_load(Path(args.constraints).read_text(encoding="utf-8"))

        input_path = Path(args.input)
        if not input_path.exists():
            raise SystemExit(f"Input not found: {input_path}")

        out = {
            "meta": {
                "status": "stub",
                "message": "Parsed constraints + input; solver not implemented yet",
                "constraints": {
                    "max_hours_per_night": constraints.get("limits", {}).get("max_hours_per_night"),
                    "max_nights": constraints.get("limits", {}).get("max_nights"),
                },
            },
            "routes": [],
        }
        Path(args.output).write_text(json.dumps(out, indent=2), encoding="utf-8")
        return
