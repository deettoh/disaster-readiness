import json
from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:root@localhost:5432/routing_db"

def get_node_id(conn, lon, lat):
    """
    Tries to find the nearest node within a 1km radius.
    If the point is too far from any road, it returns None.
    """
    snap_sql = """
        SELECT id, 
               ST_Distance(the_geom::geography, ST_SetSRID(ST_Point(:lon, :lat), 4326)::geography) as dist
        FROM pj_roads_vertices_pgr
        WHERE ST_DWithin(the_geom::geography, ST_SetSRID(ST_Point(:lon, :lat), 4326)::geography, 1000)
        ORDER BY the_geom <-> ST_SetSRID(ST_Point(:lon, :lat), 4326)
        LIMIT 1;
    """
    res = conn.execute(text(snap_sql), {"lon": lon, "lat": lat}).fetchone()
    return res[0] if res else None

def test_route_logic(start_coords, end_coords, label):
    engine = create_engine(DATABASE_URL)
    print(f"--- Testing Case: {label} ---")
    
    with engine.connect() as conn:
        # Snap Nodes
        u = get_node_id(conn, start_coords[0], start_coords[1])
        v = get_node_id(conn, end_coords[0], end_coords[1])

        if u is None or v is None:
            print(f"Result: [Input Error] Could not snap coordinates to network. "
                  f"Points are likely outside the Petaling Jaya bounds.")
            print("-" * 50)
            return

        # Check for Identical Points
        if u == v:
            print(f"Result: [Zero Distance] Start and End snapped to the same node ({u}). "
                  f"Travel time: 0s, Distance: 0m.")
            print("-" * 50)
            return

        # Run Dijkstra Pathfinding
        query = """
            SELECT count(*) 
            FROM pgr_dijkstra(
                'SELECT id, source, target, agg_cost AS cost FROM pj_roads',
                :start_node, :end_node, directed := true
            );
        """
        try:
            res = conn.execute(text(query), {"start_node": u, "end_node": v}).fetchone()
            
            if res and res[0] > 0:
                print(f"Result: [Success] Path found between Node {u} and Node {v}.")
            else:
                print(f"Result: [Routing Error] No path exists between Node {u} and Node {v}. "
                      f"The nodes are in disconnected components of the road graph.")
        except Exception as e:
            print(f"Result: [Database Error] Query failed: {e}")

    print("-" * 50)

if __name__ == "__main__":
    # Case A: Point far away from PJ (e.g., Middle of the Ocean)
    # Expected: Snapping failure
    test_route_logic((0.0, 0.0), (101.609, 3.155), "Out-of-Bounds Point")

    # Case B: Identical coordinates
    # Expected: Immediate zero-cost return
    test_route_logic((101.609, 3.155), (101.609, 3.155), "Same Start/End Point")

    # Case C: Valid snapping but disconnected island (Simulated with high/low node IDs if known)
    test_route_logic((101.609, 3.155), (101.645, 3.100), "Valid Route Check")