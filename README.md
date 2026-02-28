# RouteOPT

Roadway measurement route optimizer.

## Goal
Given a roadway network (GeoJSON) with roadway id, BMP/EMP, speed limit, and total lanes, generate nightly measurement routes (<= 4 hours/night) that minimize **deadhead distance**, subject to a **max nights** constraint.

Key constraints:
- Depot fixed at USF CUTR.
- Lane-by-lane measurement, passes must be contiguous per (roadway_id, direction) block.
- Service speed <= speed limit.

## Status
MVP scaffolding is in place. The `plan` command currently validates inputs and writes a stub output.

## Quickstart
```bash
python -m venv .venv && source .venv/bin/activate
pip install -e .

cp constraints.example.yaml constraints.yaml
routeopt plan --input your.geojson --constraints constraints.yaml --output routes.json
```

## Planning
See `planning/PLAN_v3_1.md`.


## OSM routing (optional)
To use OSM-based deadhead distances:

```bash
pip install -e '.[osm]'
# in constraints.yaml set: routing_engine: osmnx
```


## Example

```bash
cp examples/constraints.euclidean.yaml constraints.yaml
routeopt plan --input examples/sample.geojson --constraints constraints.yaml --output routes.json
cat routes.json
```
