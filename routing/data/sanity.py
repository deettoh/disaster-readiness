"""Performs graph connectivity sanity check."""

from apps.api.src.app.core.config import get_settings
from sqlalchemy import create_engine, text

settings = get_settings()

def run_sanity_checks():
    """Checks for broken road links, analyzes junctions, and runs a test route."""
    print(f"--- {settings.app_name}: Connectivity & Integrity Analysis ---")
    print(f"Target Environment: {settings.app_env.upper()}")

    db_host = settings.routing_database_url.split('@')[-1]
    print(f"Connecting to: {db_host}")

    engine = create_engine(settings.routing_database_url)

    # [1/3] Check for dangling edges
    print("\n[1/3] Checking for topological integrity...")
    integrity_sql = """
        SELECT
            (SELECT COUNT(*) FROM pj_roads WHERE source NOT IN (SELECT id FROM pj_roads_vertices_pgr)) as missing_source,
            (SELECT COUNT(*) FROM pj_roads WHERE target NOT IN (SELECT id FROM pj_roads_vertices_pgr)) as missing_target;
    """
    with engine.connect() as conn:
        result = conn.execute(text(integrity_sql)).fetchone()
        if result:
            missing_src = result[0] or 0
            missing_tgt = result[1] or 0
            if missing_src == 0 and missing_tgt == 0:
                print("Topology is clean: All edge endpoints exist in vertex table.")
            else:
                print(f"Integrity Issue: {missing_src} missing sources, {missing_tgt} missing targets.")

    # [2/3] Junction analysis
    print("\n[2/3] Analyzing Junction Complexity...")
    with engine.connect() as conn:
        junction_query = "SELECT cnt, COUNT(*) as node_count FROM pj_roads_vertices_pgr GROUP BY cnt ORDER BY cnt;"
        rows = conn.execute(text(junction_query)).fetchall()
        for row in rows:
            desc = "Dead-end/Cul-de-sac" if row[0] == 1 else f"{row[0]}-way Intersection"
            print(f" - {desc}: {row[1]} nodes")

    # [3/3] Randomized Dijkstra verification
    print("\n[3/3] Performing Randomized Pathfinding Test...")

    # This query picks two random nodes and calculates the shortest path using your agg_cost
    random_test_query = """
        WITH random_nodes AS (
            SELECT id FROM pj_roads_vertices_pgr ORDER BY RANDOM() LIMIT 2
        ),
        route AS (
            SELECT * FROM pgr_dijkstra(
                'SELECT id, source, target, agg_cost AS cost, agg_reverse_cost AS reverse_cost FROM pj_roads',
                (SELECT id FROM random_nodes LIMIT 1),
                (SELECT id FROM random_nodes OFFSET 1 LIMIT 1),
                directed := true
            )
        )
        SELECT
            SUM(r.cost) as total_time_sec,
            SUM(p.length) as total_dist_meters,
            (SELECT id FROM random_nodes LIMIT 1) as start_node,
            (SELECT id FROM random_nodes OFFSET 1 LIMIT 1) as end_node
        FROM route r
        JOIN pj_roads p ON r.edge = p.id;
    """

    with engine.connect() as conn:
        try:
            route_res = conn.execute(text(random_test_query)).fetchone()

            if route_res and route_res[0] is not None:
                time_sec = float(route_res[0])
                dist_km = float(route_res[1]) / 1000
                start_n = route_res[2]
                end_n = route_res[3]

                # Calculate speed for realism check
                avg_speed = (dist_km / (time_sec / 3600)) if time_sec > 0 else 0

                print("Dijkstra calculation successful!")
                print("-" * 35)
                print(f"Path:      Node {start_n} ➔ Node {end_n}")
                print(f"Distance:  {dist_km:.2f} km")
                print(f"Time:      {round(time_sec, 1)}s ({round(time_sec / 60, 1)} mins)")
                print(f"Avg Speed: {round(avg_speed, 1)} km/h")
                print("-" * 35)
            else:
                print("No path found between these random nodes. (Possible isolated graph segment)")

        except Exception as e:
            print(f"Pathfinding logic failed: {e}")

    print(f"\n--- Sanity Checks Completed for {settings.app_env.upper()} ---")

if __name__ == "__main__":
    run_sanity_checks()
