# Hyperlocal Disaster Readiness (Malaysia) - Routing

## Main Python Files' Details (inside disaster-readiness/routing/data/ and disaster-readiness/routing/sql/)
## Note: The files are listed in the order of implementation of routing.
| Python File | What it is for | 
| --- | --- |
| `osm_extract.py` | Downloads and exports road network data for Petaling Jaya, Malaysia, using OSMnx. |
| `load_postgres.py` | Downloads Petaling Jaya road networks and imports them into a PostGIS database for pgRouting. |
| `topology.py` | Builds the pgRouting topology by creating source/target columns and a vertex table for the PJ road network. |
| `cost.py` | Calculates base costs, initializes risk penalties, and populates aggregated cost. |
| `index.py` | Applies spatial and relational indexes to the road and vertex tables to optimize routing performance. |
| `sanity.py` | Performs graph connectivity sanity check. |
| `snapping.py` | Provides geometric 'snapping' logic for start points and end points. |
| `pgr.py` | Provides a pathfinding query to compute optimal paths using Dijkstra and A* algorithms via pgRouting. |
| `output.py` | Generates randomized route geometries output in GeoJSON format as well as distance/ETA output. |
| `edge.py` | Tests the routing engine against edge cases like out-of-bounds coordinates and identical start/end points. |
| `contract.py` | Provides a standardized query contract that returns distance, ETA, and GeoJSON geometries for any PJ coordinate pair. |
| `hazard.py` | Define penalty mapping based on hazard type and penalty scaling based on confidence score. |
| `radius.py` | Implements radius-based spatial queries and verifies penalty application and resets. |
| `updater.py` | Implements and verifies SQL-based risk penalty updates and cost recomputation. |
| `route_change.py` | Verifies that routing paths change or update their metrics after a hazard event. |
| `accessibility.py` | Implements accessibility metrics, per-cell accessibility computation and store them in table. |

## Other Folders/Files 
| Folder/File | Content | Directory |
| --- | --- | --- | 
| `pj_mvp_data` | Stores the foundational ESRI Shapefile dataset for or the pgRouting topology and the disaster-readiness engine. | `disaster-readiness/` |
| `pj_shelters.csv` | Shelter location file. | `disaster-readiness/` |
| `pj_test_scenarios.json` | File of sample coordinate pairs for testing. | `disaster-readiness/` |
| `pj_full_map_visualization.png` | Map visualization of Petaling Jaya. | `disaster-readiness/` |
| `random_route_output.geojson` | Stores the output generated from output.py. | `disaster-readiness/` |
| `pj_processed_roads.sql` | Processed roads dataset for routing. | `disaster-readiness/` |
| `map.py` | Fetches road geometries from PostGIS and generates a map visualization of Petaling Jaya. | `disaster-readiness/routing/data/` |
| `sample.py` | Generates structured JSON sample test cases representing realistic disaster evacuation scenarios across Petaling Jaya. | `disaster-readiness/routing/data/` |
| `shelter.py` | Prepare a shelter location file. | `disaster-readiness/routing/data/` |

## Query Contract for Member A (Backend)
Script to run: routing/sql/contract.py
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

## Accessibility Data Handover to Member B

1. Data Source: > * Table: cell_accessibility

View: v_accessibility_readiness (Use this for scoring)

2. Technical Specs:

Coordinate System: WGS 84 (SRID: 4326).

Logic: Travel times are computed using Dijkstra's algorithm via pgRouting, factoring in both distance and hazard penalties.

Accessibility Factor: 1.0 = fast access; 0.25 = restricted access.

3. Integration Recommendation:
You can now run a spatial join between my v_accessibility_readiness view and your population_density data.

"I have provided the 'Multiplier' (Accessibility). Multiply your population data by my factor, and you will see exactly where our disaster readiness is strongest and weakest."

Query Example: >     SELECT a.cell_id, (a.accessibility_factor * p.density) as total_readiness_score FROM v_accessibility_readiness a JOIN population_data p ON ST_Intersects(a.cell_geom, p.geom);

