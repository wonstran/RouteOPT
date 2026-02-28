# Roadway Measurement Route Optimizer: Implementation Plan v3.1

## 1. Problem Formulation

**Objective:** Minimize **total deadhead distance** subject to constraints.
**Constraint 1 (Hard):** Each nightly route duration $\le 4$ hours.
**Constraint 2 (Hard):** Total nights $\le \text{max\_nights}$ (default 200).
**Constraint 3 (Service):** All passes for a specific `(roadway_id, direction)` block must be served contiguously in the same night.

**Problem Type:** Capacitated Arc Routing Problem (CARP) with time windows and "service block" constraints.

*   **Graph:** Directed graph $G=(V,E)$ derived from OSM.
*   **Tasks:** A task is a `(roadway_id, direction)` tuple.
    *   **Demand:** $N$ passes, where $N$ is derived from `total_lanes` via a splitting rule.
    *   **Duration:** $N \times \text{TraversalTime} + (N-1) \times \text{LoopBackTime}$.
    *   **Oneway Logic:** If `oneway=true`, create 1 task (`lanes=total`). If `oneway=false`, create 2 tasks (`lanes_A`, `lanes_B`). If missing, default to `false`.
*   **Depot:** USF CUTR (Lat: 28.0585626, Lon: -82.4163460).

### Lane Splitting Rule
Input features provide `total_lanes`.
*   **Default (Balanced):** `lanes_A = ceil(total / 2)`, `lanes_B = floor(total / 2)`.
*   *Example:* 5 lanes → 3 lanes Direction A, 2 lanes Direction B.
*   *Direction A/B Inference:* Based on digitization order or azimuth.

## 2. Data Model

### 2.1 Input Schema (GeoJSON)
```json
{
  "type": "FeatureCollection",
  "features": [
    {
      "type": "Feature",
      "properties": {
        "roadway_id": "SR-60_East",
        "total_lanes": 4,
        "speed_limit": 55,
        "oneway": false
      },
      "geometry": { "type": "LineString", "coordinates": [...] }
    }
  ]
}
```

### 2.2 Configuration Example (`config.yaml`)
```yaml
# Depot Location (USF CUTR)
depot:
  lat: 28.0585626
  lon: -82.4163460

constraints:
  max_night_duration_hours: 4.0
  max_nights: 200
  oneway:
    default: false

parameters:
  service_speed_factor: 0.9  # Measure at 90% of speed limit
  deadhead_speed_factor: 1.0 # Travel at 100% of speed limit
  lane_split_strategy: "balanced"

  # Loopback Calculation Mode
  # 'constant': Add constant_seconds per turn
  # 'routing': Calculate shortest path from Segment End -> Segment Start
  loopback:
    mode: "constant" 
    constant_seconds: 60
```

### 2.3 Output Schema (JSON)
Organized by nights, then by service blocks.

```json
{
  "meta": {
    "total_nights": 5,
    "total_deadhead_miles": 150.2,
    "total_service_miles": 420.5
  },
  "routes": [
    {
      "night_index": 1,
      "date": "2024-11-01",
      "duration_hours": 3.8,
      "distance_miles": 55.0,
      "steps": [
        {
          "type": "deadhead",
          "from": "Depot",
          "to": "SR-60_East_Start",
          "duration_sec": 1800,
          "distance_miles": 20.0
        },
        {
          "type": "service_block",
          "roadway_id": "SR-60_East",
          "direction": "A",
          "azimuth": 90,
          "passes": 2,
          "duration_sec": 2400,
          "distance_miles": 10.0,
          "details": [
            { "pass": 1, "lane_virtual": "R1" },
            { "pass": 2, "lane_virtual": "R2" }
          ]
        },
        {
          "type": "deadhead",
          "from": "SR-60_East_End",
          "to": "Depot",
          "duration_sec": 1800
        }
      ]
    }
  ]
}
```

## 3. Algorithm Plan

### Phase 1: Pre-Processing & Graph Build
1.  **Ingest:** Read GeoJSON.
2.  **Split:** Apply lane splitting to generate directed tasks.
    *   *One-way:* 1 Task (`lanes = total`).
    *   *Two-way:* 2 Tasks (`lanes_A`, `lanes_B`).
3.  **Cost Estimation:**
    *   For each task, calculate `BlockDuration = (Passes * Length / ServiceSpeed) + ((Passes - 1) * LoopBackTime)`.
    *   *Pruning:* If `BlockDuration + 2 * DepotTravel > 4 hours`, the segment is too long. Split segment geometry (virtual split).

### Phase 2: Matrix Generation
1.  **POIs:** Identify Start/End coordinates for all Tasks + Depot.
2.  **OSM Routing:** Use `osmnx` graph or OSRM to compute Time/Distance matrix between all POIs.
3.  **Cache:** Save matrix to disk/memory.

### Phase 3: Optimization (Bin Packing + Routing)
Since we have a hard "contiguous block" constraint, this simplifies to a Vehicle Routing Problem (VRP) where each "Customer" is a full multi-pass service block.

**Constructive Heuristic (Parallel Clarke-Wright or Best-Fit):**
1.  Initialize $N$ empty nights (bins).
2.  Sort Tasks by "difficulty" (distance from Depot or total duration).
3.  Insert Task into the night that minimizes added deadhead, respecting the 4-hour limit.
4.  If no night fits, open a new night.

**Improvement (Local Search):**
*   **Swap:** Exchange Task A (Night 1) and Task B (Night 2).
*   **Relocate:** Move Task A from Night 1 to Night 2.
*   **Objective:** Minimize $\sum \text{Deadhead}$ (while keeping Nights $\le 200$).

## 4. Performance & Caching
*   **Graph Snapping:** Use `osmnx.distance.nearest_nodes` to map GeoJSON coordinates to the nearest OSM graph nodes. *Warning:* Ensure snapping doesn't jump across highways (check bearing/distance).
*   **Matrix Caching:** The bottleneck is `One-to-Many` routing. Compute once, store in `pickle` or `sqlite`.
    *   Key: `(node_id_from, node_id_to)` -> `(time, distance)`.

## 5. Testing & Validation
*   **Unit Tests:**
    *   `test_lane_splitting`: 5 lanes -> 3/2 split.
    *   `test_block_duration`: Verify formula includes loop-backs.
    *   `test_night_limit`: Ensure route duration never exceeds 4.0h.
*   **Validation:**
    *   **Visual:** Map plot showing contiguous blocks (all passes of Segment X happen in sequence).
    *   **Logic:** Sum of serviced miles should exactly equal `Input Miles * Total Lanes`.
*   **Edge Cases:**
    *   Isolated segments (unreachable).
    *   Segments requiring > 4h (must split geometry).
