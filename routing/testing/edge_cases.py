"""Tests the routing engine against edge cases like out-of-bounds coordinates and identical start/end points."""

from apps.api.src.app.core.config import get_settings
from sqlalchemy import create_engine, text

settings = get_settings()

def get_node_id(conn, lon, lat):
    """Attempts to find the nearest node ID within 1km of the coordinates using spatial indexing."""
    # This uses the <-> operator for fast KNN (nearest neighbor) search
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
    """Verifies routing behavior for out-of-bounds, identical, or disconnected points."""
    engine = create_engine(settings.routing_database_url)

    print(f"\n[Case: {label}]")

    with engine.connect() as conn:
        # Snap Nodes to the nearest vertex
        u = get_node_id(conn, start_coords[0], start_coords[1])
        v = get_node_id(conn, end_coords[0], end_coords[1])

        # Check for Out-of-Bounds (Snapping Failure)
        if u is None or v is None:
            print("Result: [Input Error] Coordinates could not be snapped.")
            print("Hint: Points are likely outside the Petaling Jaya service area.")
            return

        # Check for Identical Points (Zero Distance)
        if u == v:
            print(f"Result: [Zero Distance] Start and End snapped to the same node ({u}).")
            print("Logic: Return 0s duration and 0m distance immediately.")
            return

        # Run Dijkstra to check for Graph Connectivity
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
                print(f"Result: [Success] Valid path exists between Node {u} and Node {v}.")
            else:
                print(f"Result: [Graph Error] No path exists between Node {u} and Node {v}.")
                print("Hint: These points might be on disconnected 'island' road segments.")
        except Exception as e:
            print(f"Result: [Database Error] Query failed: {e}")


if __name__ == "__main__":
    # Standard API-Ready Header
    print(f"--- {settings.app_name}: Edge Case Validation ---")
    print(f"Target Environment: {settings.app_env.upper()}")

    db_host = settings.routing_database_url.split('@')[-1]
    print(f"Testing against: {db_host}")
    print("=" * 50)

    # Case A: Out-of-Bounds (Atlantic Ocean/Null Island)
    test_route_logic((0.0, 0.0), (101.609, 3.155), "Out-of-Bounds Point")

    # Case B: Identical coordinates (User is already at the shelter)
    test_route_logic((101.609, 3.155), (101.609, 3.155), "Same Start/End Point")

    # Case C: Valid route check (Typical PJ journey)
    test_route_logic((101.609, 3.155), (101.645, 3.100), "Standard Valid Route")

    print("\n" + "=" * 50)
    print(f"Edge case testing completed for {settings.app_env.upper()}.")
