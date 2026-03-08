"""Generates randomized route geometries output in GeoJSON format as well as distance/ETA output."""

import json
from pathlib import Path

from apps.api.src.app.core.config import get_settings
from sqlalchemy import create_engine, text

settings = get_settings()

# Define Artifacts directory relative to this file
ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"

def get_random_node_ids(conn):
    """Picks two random node IDs from the road network."""
    query = "SELECT id FROM pj_roads_vertices_pgr ORDER BY RANDOM() LIMIT 2;"
    try:
        result = conn.execute(text(query)).fetchall()
        if len(result) >= 2:
            return result[0][0], result[1][0]
        return None, None
    except Exception as e:
        print(f"Database error picking nodes: {e}")
        return None, None

def get_route_output_by_nodes(start_node, end_node):
    """Generates GeoJSON geometries and travel metrics for randomized routes."""
    engine = create_engine(settings.database_url)

    # PostGIS query to aggregate segments into a single LineString GeoJSON
    route_query = """
        WITH path AS (
            SELECT * FROM pgr_dijkstra(
                'SELECT id, source, target, agg_cost AS cost, agg_reverse_cost AS reverse_cost FROM pj_roads',
                :start_node, :end_node, directed := true
            )
        ),
        route_segments AS (
            SELECT p.seq, r.length, r.agg_cost, r.geometry
            FROM path p
            JOIN pj_roads r ON p.edge = r.id
            ORDER BY p.seq
        )
        SELECT
            SUM(length) as total_dist_m,
            SUM(agg_cost) as total_time_s,
            ST_AsGeoJSON(ST_LineMerge(ST_Collect(geometry))) as geojson_geom
        FROM route_segments;
    """

    with engine.connect() as conn:
        print(f"Routing: Node {start_node} ➔ Node {end_node}")
        try:
            result = conn.execute(
                text(route_query), {"start_node": start_node, "end_node": end_node}
            ).fetchone()
        except Exception as e:
            print(f"Routing logic error: {e}")
            return None

        if not result or result[2] is None:
            print("No valid path found between these nodes.")
            return None

        total_dist_meters = result[0] or 0
        total_time_seconds = result[1] or 0
        geojson_geometry = json.loads(result[2])

        return {
            "task_4_geojson": {
                "type": "Feature",
                "geometry": geojson_geometry,
                "properties": {
                    "source": start_node,
                    "target": end_node,
                    "env": settings.app_env
                },
            },
            "task_5_metrics": {
                "distance_km": round(total_dist_meters / 1000, 2),
                "eta_minutes": round(total_time_seconds / 60, 2),
            },
        }

def verify_outputs(data):
    """Prints a summary of the generated route geometry and performance metrics."""
    if not data:
        return

    metrics = data["task_5_metrics"]
    print("\n--- Route Verification Report ---")
    print(f"GeoJSON Type: {data['task_4_geojson']['geometry']['type']}")
    print(f"Distance:     {metrics['distance_km']} km")
    print(f"ETA:          {metrics['eta_minutes']} minutes")
    print("-" * 33)

if __name__ == "__main__":
    # Header with Environment Prompt
    print(f"--- {settings.app_name}: Randomized Route Export ---")
    print(f"Target Environment: {settings.app_env.upper()}")

    db_host = settings.database_url.split('@')[-1]
    print(f"Connecting to: {db_host}\n")

    engine = create_engine(settings.database_url)

    with engine.connect() as conn:
        node_a, node_b = get_random_node_ids(conn)

    if node_a and node_b:
        route_results = get_route_output_by_nodes(node_a, node_b)

        if route_results:
            verify_outputs(route_results)

            # Save to Artifacts
            ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
            output_file = ARTIFACTS_DIR / "random_route_output.geojson"

            with output_file.open("w", encoding="utf-8") as f:
                json.dump(route_results["task_4_geojson"], f, indent=2)

            print(f"Success: GeoJSON saved to {output_file}")
    else:
        print("Could not retrieve random nodes. Check vertex table connectivity.")
