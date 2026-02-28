from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache

from routeopt.utils.geo import LatLon, haversine_miles


@dataclass(frozen=True)
class DistTime:
    distance_miles: float
    duration_hours: float


@dataclass
class EuclideanRouting:
    deadhead_speed_mph: float

    def dist_time(self, a: LatLon, b: LatLon) -> DistTime:
        mi = haversine_miles(a, b)
        h = mi / max(1e-6, self.deadhead_speed_mph)
        return DistTime(distance_miles=mi, duration_hours=h)


class OSMnxRouting:
    """OSMnx-based shortest path routing (distance + time).

    This is an optional mode intended for more realistic deadhead legs.

    Notes:
    - Requires the optional dependencies group: `pip install -e .[osm]`
    - Builds an OSM drive graph covering the bbox of all task endpoints + depot,
      with a configurable buffer.
    """

    def __init__(
        self,
        *,
        depot: LatLon,
        points: list[LatLon],
        buffer_miles: float,
        deadhead_speed_mph: float,
    ):
        try:
            import osmnx as ox
            import networkx as nx
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "OSMnxRouting requires optional dependencies. Install with: pip install -e '.[osm]'"
            ) from e

        self._ox = ox
        self._nx = nx
        self._deadhead_speed_mph = max(1e-6, deadhead_speed_mph)

        all_pts = [depot, *points]
        lats = [p.lat for p in all_pts]
        lons = [p.lon for p in all_pts]

        # expand bbox by buffer miles (approx degrees)
        dlat = buffer_miles / 69.0
        dlon = buffer_miles / (69.0 * max(1e-6, abs(__import__("math").cos(__import__("math").radians(sum(lats)/len(lats))))))

        north = max(lats) + dlat
        south = min(lats) - dlat
        east = max(lons) + dlon
        west = min(lons) - dlon

        self._G = ox.graph_from_bbox(north, south, east, west, network_type="drive")
        # add travel_time edge attribute (hours) using deadhead speed
        for u, v, k, data in self._G.edges(keys=True, data=True):
            length_m = float(data.get("length", 0.0))
            miles = length_m / 1609.344
            data["_dist_miles"] = miles
            data["_time_h"] = miles / self._deadhead_speed_mph

    @lru_cache(maxsize=100_000)
    def _nearest_node(self, lat: float, lon: float) -> int:
        return int(self._ox.distance.nearest_nodes(self._G, X=lon, Y=lat))

    @lru_cache(maxsize=200_000)
    def _shortest_dist_time(self, a_node: int, b_node: int) -> DistTime:
        # shortest by distance
        path = self._nx.shortest_path(self._G, a_node, b_node, weight="_dist_miles")
        dist = 0.0
        time_h = 0.0
        for u, v in zip(path, path[1:]):
            # choose min over parallel edges
            edges = self._G.get_edge_data(u, v)
            best = None
            for _k, d in edges.items():
                cand = float(d.get("_dist_miles", 0.0))
                if best is None or cand < best[0]:
                    best = (cand, float(d.get("_time_h", 0.0)))
            if best:
                dist += best[0]
                time_h += best[1]
        return DistTime(distance_miles=dist, duration_hours=time_h)

    def dist_time(self, a: LatLon, b: LatLon) -> DistTime:
        a_node = self._nearest_node(a.lat, a.lon)
        b_node = self._nearest_node(b.lat, b.lon)
        return self._shortest_dist_time(a_node, b_node)
