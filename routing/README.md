# Routing (pgRouting)

This module implements the dynamic evacuation routing engine for the Hyperlocal Disaster Readiness platform. It uses pgRouting on top of PostGIS to compute shortest path evacuation routes that automatically reroute around hazardous road segments.

## Pipeline

OSM Road Extract → Graph Import → Topology Build → Cost Initialization → pgRouting Queries → Dynamic Penalty Updates → Accessibility Metrics

## How It Works

1. **Road graph** is built from OpenStreetMap data for Petaling Jaya
2. **Base costs** are computed from road segment length and type
3. **Risk penalties** are initialized at zero and updated dynamically when hazards are reported
4. **Route cost** = `base_cost + risk_penalty` — penalized roads are avoided by the pathfinding algorithm
5. **Accessibility metrics** (travel time to shelters, road density) are computed per grid cell and fed into the readiness score engine

## Data Requirements

| Dataset | Source | Format | Description |
| :--- | :--- | :--- | :--- |
| **OSM Road Network** | [OpenStreetMap](https://www.openstreetmap.org/node/254073469#map=15/3.09475/101.65229) | `.pbf` | Road network extract for Petaling Jaya with geographical coordinates for shelter locations |
| **SRTM Elevation** | [OpenTopography — SRTM GL1](https://portal.opentopography.org/raster?opentopoID=OTSRTM.082015.4326.1) | `.hgt` | Elevation raster used for slope-based features and accessibility analysis |

### Notes and Limitations

- The `.pbf` file extracts raw geometry which requires further processing (topology build, cost computation) before it is usable for routing
- OSM data is a snapshot in time and is not synced with real-time road conditions
- OSM shapefiles are generated locally under `routing/data/pj_mvp_data/` and are not committed to the repository

## Setup

Run these steps in order from the repository root.

### Prerequisites

```bash
poetry install
```

Ensure your database is reachable via `DATABASE_URL`:
```
postgresql://postgres.<PROJECT_REF>:<DB_PASSWORD>@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres?sslmode=require
```

### Generate Routing Artifacts (run in order)

Before building the routing database, you must process the raw OSM data into routable artifacts. Run these scripts to generate the local graph data, apply topology, and calculate initial edge costs:

```bash
# 1. Download and extract OSM road data for Petaling Jaya
poetry run python -m routing.data.src.osm_extract

# 2. Load the extracted road network into PostGIS
poetry run python -m routing.data.src.load_postgres

# 3. Build graph topology (source/target nodes)
poetry run python -m routing.data.src.topology

# 4. Compute base routing costs and initialize risk penalties
poetry run python -m routing.data.src.cost

# 5. Apply database indexes for routing performance
poetry run python -m routing.data.src.index

# 6. Run sanity checks on graph connectivity
poetry run python -m routing.data.src.sanity

# 7. (Optional) Generate a map visualization of the road network
poetry run python -m routing.data.src.map

# 8. Extract shelter candidates to CSV
poetry run python -m routing.data.src.shelter
```

### Build Routing Database (run in order)

```bash
# 1. Reset DB (applies migrations + seed data)
supabase db reset

# 2. Import Petaling Jaya road network into public.roads_edges
poetry run python routing/scripts/import_roads.py

# 3. Generate 500m analysis grid
poetry run python routing/scripts/generate_grid.py

# 4. Compute accessibility metrics (travel times + road density)
poetry run python routing/scripts/run_accessibility.py

# 5. Verify setup (optional)
poetry run python routing/scripts/verify_sql.py
```

### Enable SQL Backend in API

Set in `.env`:

```dotenv
ROUTING_BACKEND=sql
DATABASE_URL=postgresql://postgres.<PROJECT_REF>:<DB_PASSWORD>@...
ROUTING_ALGORITHM=dijkstra
```



## Folder Structure

```text
routing/
├── artifacts/              # Generated outputs (pj_shelters.csv, route GeoJSON, map PNG)
├── data/                   # Data acquisition and graph preparation scripts
│   └── src/
│       ├── cost.py         # Computes base costs, initializes risk penalties
│       ├── index.py        # Applies routing-critical indexes
│       ├── load_postgres.py# Imports road network into PostGIS
│       ├── map.py          # Generates road network visualization
│       ├── osm_extract.py  # Downloads & exports road network data (OSMnx)
│       ├── sanity.py       # Runs graph connectivity checks
│       ├── shelter.py      # Extracts shelter candidates to CSV
│       └── topology.py     # Builds source/target topology and vertex table
├── scripts/                # CLI runner scripts for import, grid generation, accessibility
├── sql/                    # Core pgRouting query logic and penalty updates
│   ├── accessibility.py    # Computes metrics and exports CSV handoff
│   ├── contract.py         # Standardized route contract for API integration
│   ├── engine.py           # Database engine helper
│   ├── hazard.py           # Hazard label → penalty mapping
│   ├── pgr.py              # Dijkstra and A* pathfinding via pgRouting
│   ├── radius.py           # Radius-based spatial queries for penalty application
│   ├── route_change.py     # Verifies route changes after hazard events
│   ├── snapping.py         # Start/end point geometric snapping
│   └── updater.py          # SQL-based risk penalty updates and cost recomputation
└── testing/                # Routing QA/demo scripts and test fixtures
```

## Schema Compatibility

Canonical routing storage is `public.roads_edges`. To avoid routing service code churn, Supabase migration `20260305143000_add_routing_compatibility_views.sql` exposes legacy contract objects:

- `public.pj_roads` (compatibility view)
- `public.pj_roads_vertices_pgr` (compatibility materialized view)

After structural road updates, refresh with:
```sql
SELECT public.refresh_pj_roads_vertices_pgr();
```

## Shelter Data

If the frontend needs shelter points, generate `routing/artifacts/pj_shelters.csv`:

```bash
poetry run python -m routing.data.src.shelter
```

Frontend `npm run dev` / `npm run build` auto-syncs this file into `apps/frontend/public/pj_shelters.csv`.
