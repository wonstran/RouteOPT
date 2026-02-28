import argparse


def main(argv=None):
    p = argparse.ArgumentParser(prog="routeopt")
    sub = p.add_subparsers(dest="cmd", required=True)

    plan = sub.add_parser("plan", help="Generate nightly measurement routes")
    plan.add_argument("--input", required=True, help="Input GeoJSON file")
    plan.add_argument("--constraints", required=True, help="Constraints YAML")
    plan.add_argument("--output", default="routes.json", help="Output routes JSON")

    args = p.parse_args(argv)

    if args.cmd == "plan":
        raise SystemExit("MVP: planning pipeline not implemented yet")
