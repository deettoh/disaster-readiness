# Hyperlocal Disaster Readiness (Malaysia) - Routing

## SQL Routing Backend Setup (for API `ROUTING_BACKEND=sql`)

Run these steps from repository root.

### Prerequisites

1. Install dependencies:
  ```bash
  poetry install
  ```
2. Ensure your database is reachable via `DATABASE_URL`:
  ```
  postgresql://postgres.<PROJECT_REF>:<DB_PASSWORD>@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require
  ```
  Routing SQL scripts read `DATABASE_URL` directly.

### Build routing database objects (run in order)

1. **Reset Database**: Initialise schema and seed static shelter reference data.
  ```bash
  supabase db reset
  ```
2. **Import Road Network**: Load Petaling Jaya road edges (OSM) into `public.roads_edges`. This uses a pre-processed pg_dump and syncs it with the canonical schema.
  ```bash
  poetry run python routing/scripts/import_roads.py
  ```
3. **Generate Grid**: Generate a 500m x 500m analysis grid clipped to the PJ boundary and upload to `public.grid_cells`.
  ```bash
  poetry run python routing/scripts/generate_grid.py
  ```
4. **Compute Accessibility Metrics**: Calculate travel times to shelters and road densities for each grid cell.
  ```bash
  poetry run python routing/scripts/run_accessibility.py
  ```
5. **Verify (Optional)**: Run the end-to-end integration validator.
  ```bash
  poetry run python routing/scripts/verify_sql.py
  ```

### Enable SQL backend in API

Set in `.env`:

```dotenv
ROUTING_BACKEND=sql
DATABASE_URL=postgresql://postgres.<PROJECT_REF>:<DB_PASSWORD>@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require
ROUTING_ALGORITHM=dijkstra
```

Then start the API (Docker or non-Docker) from the root project runbook in [`README.md`](../README.md#2-run-with-docker).


Note:
- OSM shapefiles are generated locally under `routing/data/pj_mvp_data` and are not meant to be committed.
- If frontend needs shelter points, generate `routing/artifacts/pj_shelters.csv` with:
  ```bash
  poetry run python -m routing.data.src.shelter
  ```
- Frontend `npm run dev`/`npm run build` auto-syncs this file into `apps/frontend/public/pj_shelters.csv`.

## Supabase schema compatibility layer

Canonical routing storage is `public.roads_edges`.

To avoid routing service logic churn, Supabase migration
`20260305143000_add_routing_compatibility_views.sql` exposes compatibility
objects expected by the current routing contract:
- `public.pj_roads` (compatibility view)
- `public.pj_roads_vertices_pgr` (compatibility materialized view)

After structural road updates, refresh vertices with:
```sql
SELECT public.refresh_pj_roads_vertices_pgr();
```

## Folder Structure (Current)

| Path | Purpose |
| --- | --- |
| `routing/data` | Data acquisition and graph preparation scripts for Petaling Jaya routing. |
| `routing/sql` | Core pgRouting query logic and backend contract module (currently reads compatibility objects backed by `public.roads_edges`). |
| `routing/testing` | Routing QA/demo scripts (edge-case checks, scenario generation, sample output). |
| `routing/testing/fixtures` | Routing test fixture data (`pj_test_scenarios.json`). |
| `routing/artifacts` | Generated routing artifacts (`pj_shelters.csv`, map PNG, route GeoJSON). |
| `routing/data/pj_mvp_data` | Raw ESRI Shapefile dataset used to seed the route graph. |

## Python Modules

| Module | What it is for |
| --- | --- |
| `routing/data/src/osm_extract.py` | Downloads and exports road network data for Petaling Jaya using OSMnx. |
| `routing/data/src/load_postgres.py` | Imports Petaling Jaya road networks into PostGIS/pgRouting. |
| `routing/data/src/topology.py` | Builds `source`/`target` topology and the routing vertex table. |
| `routing/data/src/cost.py` | Computes base costs, initializes risk penalties, and aggregates route costs. |
| `routing/data/src/index.py` | Applies routing-critical indexes to roads and vertices tables. |
| `routing/data/src/sanity.py` | Runs graph integrity/connectivity sanity checks. |
| `routing/data/src/map.py` | Generates full road-network visualization PNG into `routing/artifacts`. |
| `routing/data/src/shelter.py` | Extracts and saves shelter candidates into `routing/artifacts/pj_shelters.csv`. |
| `routing/sql/snapping.py` | Implements start/end geometric snapping helpers. |
| `routing/sql/pgr.py` | Provides pathfinding with Dijkstra and A* using pgRouting. |
| `routing/sql/contract.py` | Standardized route contract for backend integration. |
| `routing/sql/engine.py` | Database engine helper for routing SQL modules. |
| `routing/sql/hazard.py` | Define penalty mapping based on hazard type and penalty scaling based on confidence score. |
| `routing/sql/radius.py` | Implements radius-based spatial queries and verifies penalty application and resets. |
| `routing/sql/updater.py` | Implements and verifies SQL-based risk penalty updates and cost recomputation. |
| `routing/sql/route_change.py` | Verifies that routing paths change or update their metrics after a hazard event. |
| `routing/sql/accessibility.py` | Computes canonical `public.cell_accessibility` metrics and exports CSV handoff for readiness integration. |
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
