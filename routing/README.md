# Hyperlocal Disaster Readiness (Malaysia) - Routing

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

## Query Contract for Member A (Backend)
Function: get_route(start_lat, start_lon, end_lat, end_lon, algorithm="dijkstra")

Input:
| Input | Data Type | Description |
| --- | --- | --- |
| `start_lat / lon` | float | WGS84 coordinates of the user. |
| `end_lat / lon` | float | WGS84 coordinates of the destination/shelter. |
| `algorithm` | string | "dijkstra" (standard) or "astar" (faster for long distances). |

Output (If Success):
{
  "status": "success",
  "distance_km": 5.42,
  "eta_minutes": 12.5,
  "geojson": { "type": "Feature", "geometry": { "type": "LineString", "coordinates": [...] } }
}
