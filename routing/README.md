# Hyperlocal Disaster Readiness (Malaysia) - Routing

## Python Files' Details

| Python File | What it is for | 
| --- | --- |
| `osm.py` | Downloads and exports road network data for Petaling Jaya, Malaysia, using OSMnx. |
| `postgres.py` | Downloads Petaling Jaya road networks and imports them into a PostGIS database for pgRouting. |
| `topology.py` | Builds the pgRouting topology by creating source/target columns and a vertex table for the PJ road network. |
| `cost.py` | Calculates base costs, initializes risk penalties, and populates aggregated cost. |
| `index.py` | Applies spatial and relational indexes to the road and vertex tables to optimize routing performance. |
| `sanity.py` | Performs graph connectivity sanity check. |
| `snapping.py` | Provides geometric 'snapping' logic for start points and end points. |
| `pgr.py` | Provides a pathfinding query to compute optimal paths using Dijkstra and A* algorithms via pgRouting. |
| `output.py` | Generates randomized route geometries output in GeoJSON format as well as distance/ETA output. |
| `edge.py` | Tests the routing engine against edge cases like out-of-bounds coordinates and identical start/end points. |
| `contract.py` | Provides a standardized query contract that returns distance, ETA, and GeoJSON geometries for any PJ coordinate pair. |

## Other Folders/Files
| Folder/File | Content | 
| --- | --- |
| `pj_mvp_data` | Stores the foundational ESRI Shapefile dataset for or the pgRouting topology and the disaster-readiness engine. |
| `pj_shelters.csv` | Shelter location file. |
| `pj_test_scenarios.json` | File of sample coordinate pairs for testing. |
| `pj_full_map_visualization.png` | Map visualization of Petaling Jaya. |
| `random_route_output.geojson` | Stores the output generated from output.py |

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