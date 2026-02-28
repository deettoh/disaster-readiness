"""Provides a pathfinding query to compute optimal paths using Dijkstra and A* algorithms via pgRouting."""


from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:root@localhost:5432/routing_db"


def get_node_id(conn, lon, lat):
    """Finds the nearest road network node ID for a pair of coordinates."""
    # Using the KNN operator <-> for high-performance spatial indexing
    snap_sql = """
        SELECT id FROM pj_roads_vertices_pgr
        ORDER BY the_geom <-> ST_SetSRID(ST_Point(:lon, :lat), 4326)
        LIMIT 1;
    """
    res = conn.execute(text(snap_sql), {"lon": lon, "lat": lat}).fetchone()
    return res[0] if res else None


def run_route(start_coords, end_coords, algorithm="dijkstra"):
    """Executes a pathfinding query (Dijkstra or A*) and returns the travel time and geometry."""
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # Snap coordinates to graph nodes
        start_node = get_node_id(conn, start_coords[0], start_coords[1])
        end_node = get_node_id(conn, end_coords[0], end_coords[1])

        if not start_node or not end_node:
            return "Error: Could not snap coordinates to road network."

        print(
            f"--- Calculating {algorithm.upper()} Path: {start_node} -> {end_node} ---"
        )

        # Define Queries
        dijkstra_sql = """
            SELECT
                path.seq, path.node, path.edge, path.cost,
                ST_AsGeoJSON(roads.geometry)::json as geom
            FROM pgr_dijkstra(
                'SELECT id, source, target, agg_cost AS cost, agg_reverse_cost AS reverse_cost FROM pj_roads',
                :start, :end, directed := true
            ) AS path
            LEFT JOIN pj_roads AS roads ON path.edge = roads.id
            ORDER BY path.seq;
        """

        astar_sql = """
            SELECT
                path.seq, path.node, path.edge, path.cost,
                ST_AsGeoJSON(roads.geometry)::json as geom
            FROM pgr_astar(
                'SELECT id, source, target, agg_cost AS cost, agg_reverse_cost AS reverse_cost,
                 ST_X(ST_StartPoint(geometry)) AS x1, ST_Y(ST_StartPoint(geometry)) AS y1,
                 ST_X(ST_EndPoint(geometry)) AS x2, ST_Y(ST_EndPoint(geometry)) AS y2
                 FROM pj_roads',
                :start, :end, directed := true, heuristic := 5
            ) AS path
            LEFT JOIN pj_roads AS roads ON path.edge = roads.id
            ORDER BY path.seq;
        """

        query = astar_sql if algorithm.lower() == "astar" else dijkstra_sql

        # Execute Pathfinding
        results = conn.execute(text(query), {"start": start_node, "end": end_node}).fetchall()


        # Execute Pathfinding
        results = conn.execute(
            text(query), {"start": start_node, "end": end_node}
        ).fetchall()

        if not results or len(results) <= 1:
            print("No path found.")
            return None

        # Process Results
        total_cost = sum(row[3] for row in results if row[3] > 0)
        path_geometry = [row[4] for row in results if row[4] is not None]

        print("Route Found!")
        print(f"Estimated Travel Time: {round(total_cost / 60, 2)} minutes")
        print(f"Segments traversed: {len(path_geometry)}")
        return {"travel_time_min": round(total_cost / 60, 2), "segments": path_geometry}


if __name__ == "__main__":
    # Example coordinates in Petaling Jaya
    START = (101.609, 3.155) # Mutiara Damansara
    END = (101.645, 3.100)   # PJ State

    START = (101.609, 3.155)  # Mutiara Damansara
    END = (101.645, 3.100)  # PJ State


    # Run Dijkstra
    route_data = run_route(START, END, algorithm="dijkstra")

    # Run A*
    route_data_astar = run_route(START, END, algorithm="astar")
