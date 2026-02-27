import json
import sys
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:root@localhost:5432/routing_db"

def get_random_node_ids(conn):
    """
    Retrieves two random node IDs from the vertex table.
    """
    query = "SELECT id FROM pj_roads_vertices_pgr ORDER BY RANDOM() LIMIT 2;"
    try:
        result = conn.execute(text(query)).fetchall()
        if len(result) >= 2:
            return result[0][0], result[1][0]
        else:
            print("Error: Not enough nodes found in pj_roads_vertices_pgr.")
            return None, None
    except Exception as e:
        print(f"Database error while fetching random nodes: {e}")
        return None, None

def get_route_output_by_nodes(start_node, end_node):
    """
    Performs routing between two node IDs and returns GeoJSON and metrics.
    Fulfills C2 Task 4 and Task 5.
    """
    engine = create_engine(DATABASE_URL)
    
    # Routing, Geometry Aggregation, and Metrics Query
    route_query = """
        WITH path AS (
            SELECT * FROM pgr_dijkstra(
                'SELECT id, source, target, agg_cost AS cost, agg_reverse_cost AS reverse_cost FROM pj_roads',
                :start_node, :end_node, directed := true
            )
        ),
        route_segments AS (
            SELECT 
                p.seq,
                r.length,
                r.agg_cost,
                r.geometry
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
        print(f"Attempting route from Random Node {start_node} to Random Node {end_node}")

        # Execute Routing
        try:
            result = conn.execute(text(route_query), {
                "start_node": start_node,
                "end_node": end_node
            }).fetchone()
        except Exception as e:
            print(f"Error executing routing query: {e}")
            return None

        if not result or result[2] is None:
            print("Status: No path found between these nodes (nodes may be in disconnected clusters).")
            return None

        total_dist_meters = result[0]
        total_time_seconds = result[1]
        geojson_geometry = json.loads(result[2])

        return {
            "task_4_geojson": {
                "type": "Feature",
                "geometry": geojson_geometry,
                "properties": {
                    "source_node": start_node,
                    "target_node": end_node
                }
            },
            "task_5_metrics": {
                "distance_meters": round(total_dist_meters, 2),
                "distance_km": round(total_dist_meters / 1000, 2),
                "eta_seconds": round(total_time_seconds, 2),
                "eta_minutes": round(total_time_seconds / 60, 2)
            }
        }

def verify_outputs(data):
    """Prints the verification report for Task 4 and 5."""
    if not data:
        return

    print("--- Verification: Route Geometry ---")
    geom_type = data["task_4_geojson"]["geometry"]["type"]
    coords_count = len(data["task_4_geojson"]["geometry"]["coordinates"])
    print(f"GeoJSON Type: {geom_type}")
    print(f"Geometry Nodes Found: {coords_count}")

    print("\n--- Verification: Distance/ETA ---")
    metrics = data["task_5_metrics"]
    print(f"Total Distance: {metrics['distance_km']} km")
    print(f"Estimated Travel Time: {metrics['eta_minutes']} minutes")
    
    # Simple sanity check for speed
    if metrics['eta_minutes'] > 0:
        avg_speed = metrics['distance_km'] / (metrics['eta_minutes'] / 60)
        print(f"Calculated Avg Speed: {round(avg_speed, 2)} km/h")
    print("-----------------------------------------------")

if __name__ == "__main__":
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        # Step 1: Get two random node IDs from the database
        node_a, node_b = get_random_node_ids(conn)

    if node_a and node_b:
        # Step 2: Run the routing engine using these IDs
        route_results = get_route_output_by_nodes(node_a, node_b)
        
        if route_results:
            verify_outputs(route_results)
            
            # Save to file
            filename = "random_route_output.geojson"
            with open(filename, "w") as f:
                json.dump(route_results["task_4_geojson"], f, indent=2)
            print(f"Success: Randomized route saved to {filename}")
        else:
            print("Hint: Run the script again to try a different random pair.")
    else:
        print("Routing aborted due to node retrieval failure.")