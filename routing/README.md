# Hyperlocal Disaster Readiness (Malaysia) - Routing


## SQL Routing Backend Setup (for API `ROUTING_BACKEND=sql`)

Run these steps from repository root.

### Prerequisites

1. Install dependencies:
  ```bash
  poetry install
  ```
2. Ensure PostgreSQL is running and reachable at:
  ```
  postgresql://postgres:root@localhost:5432/routing_db
  ```
  If your DB URL is different, update the `DATABASE_URL` values in the routing scripts or set your environment accordingly.

### Build routing database objects (run in order)

1. Import roads and enable PostGIS/pgRouting:
  ```bash
  poetry run python -m routing.data.postgres
  ```
2. Build topology and vertices table:
  ```bash
  poetry run python -m routing.data.topology
  ```
3. Compute costs and directional aggregated costs:
  ```bash
  poetry run python -m routing.data.cost
  ```
4. Apply routing indexes:
  ```bash
  poetry run python -m routing.data.index
  ```
5. Optional sanity validation:
  ```bash
  poetry run python -m routing.data.sanity
  ```

### Enable SQL backend in API

Set in `.env`:

```dotenv
ROUTING_BACKEND=sql
ROUTING_DATABASE_URL=postgresql://postgres:root@localhost:5432/routing_db
ROUTING_ALGORITHM=dijkstra
```

Then start the API (Docker or non-Docker) from the root project runbook in [`README.md`](../README.md#2-run-with-docker).

Note:
- OSM shapefiles are generated locally under `routing/data/pj_mvp_data` and are not meant to be committed.
- If frontend needs shelter points, generate `routing/artifacts/pj_shelters.csv` with:
  ```bash
  poetry run python -m routing.data.shelter
  ```
- Frontend `npm run dev`/`npm run build` auto-syncs this file into `apps/frontend/public/pj_shelters.csv`.

## Folder Structure (Current)

| Path | Purpose |
| --- | --- |
| `routing/data` | Data acquisition and graph preparation scripts for Petaling Jaya routing. |
| `routing/sql` | Core pgRouting query logic and backend contract module. |
| `routing/testing` | Routing QA/demo scripts (edge-case checks, scenario generation, sample output). |
| `routing/testing/fixtures` | Routing test fixture data (`pj_test_scenarios.json`). |
| `routing/artifacts` | Generated routing artifacts (`pj_shelters.csv`, map PNG, route GeoJSON). |
| `routing/data/pj_mvp_data` | Raw ESRI Shapefile dataset used to seed the route graph. |

## Python Modules

| Module | What it is for |
| --- | --- |
| `routing/data/osm.py` | Downloads and exports road network data for Petaling Jaya using OSMnx. |
| `routing/data/postgres.py` | Imports Petaling Jaya road networks into PostGIS/pgRouting. |
| `routing/data/topology.py` | Builds `source`/`target` topology and the routing vertex table. |
| `routing/data/cost.py` | Computes base costs, initializes risk penalties, and aggregates route costs. |
| `routing/data/index.py` | Applies routing-critical indexes to roads and vertices tables. |
| `routing/data/sanity.py` | Runs graph integrity/connectivity sanity checks. |
| `routing/data/map.py` | Generates full road-network visualization PNG into `routing/artifacts`. |
| `routing/data/shelter.py` | Extracts and saves shelter candidates into `routing/artifacts/pj_shelters.csv`. |
| `routing/sql/snapping.py` | Implements start/end geometric snapping helpers. |
| `routing/sql/pgr.py` | Provides pathfinding with Dijkstra and A* using pgRouting. |
| `routing/sql/contract.py` | Standardized route contract for backend integration. |
| `routing/testing/edge_cases.py` | Validates route behavior for out-of-bounds/same-node/disconnected cases. |
| `routing/testing/random_route_output.py` | Generates randomized route GeoJSON output into `routing/artifacts`. |
| `routing/testing/scenario_generator.py` | Generates routing test scenario fixtures into `routing/testing/fixtures`. |

## Query Contract for Backend
Function: get_route(start_lat, start_lon, end_lat, end_lon, algorithm="dijkstra")

Input:
| Input | Data Type | Description |
| --- | --- | --- |
| `start_lat / lon` | float | WGS84 coordinates of the user. |
| `end_lat / lon` | float | WGS84 coordinates of the destination/shelter. |
| `algorithm` | string | "dijkstra" (standard) or "astar" (faster for long distances). |

Output (If Success):
```bash
{
  "status": "success",
  "distance_km": 5.42,
  "eta_minutes": 12.5,
  "geojson": { "type": "Feature", "geometry": { "type": "LineString", "coordinates": [...] } }
}
```