# RouteOPT

Roadway measurement route optimizer.

## Goal
Generate nightly (<= 4 hours) measurement routes from a GeoJSON roadway network, minimizing deadhead distance under a max-nights constraint.

## CLI (planned)
```bash
routeopt plan --input roads.geojson --constraints constraints.yaml --output routes.json
```
