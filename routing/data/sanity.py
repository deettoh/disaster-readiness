from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:root@localhost:5432/routing_db"

def run_sanity_checks():
    engine = create_engine(DATABASE_URL)
    print("--- Graph Connectivity & Integrity Analysis ---")

    # [1/3] CHECK FOR DANGLING EDGES
    print("\n[1/3] Checking for topological integrity...")
    integrity_sql = """
        SELECT 
            (SELECT COUNT(*) FROM pj_roads WHERE source NOT IN (SELECT id FROM pj_roads_vertices_pgr)) as missing_source,
            (SELECT COUNT(*) FROM pj_roads WHERE target NOT IN (SELECT id FROM pj_roads_vertices_pgr)) as missing_target;
    """
    with engine.connect() as conn:
        result = conn.execute(text(integrity_sql)).fetchone()
        if result is not None:
            missing_src = result[0] or 0
            missing_tgt = result[1] or 0
            if missing_src == 0 and missing_tgt == 0:
                print("Topology is clean: All edge endpoints exist in vertex table.")
            else:
                print(f"Integrity Issue: {missing_src} missing sources, {missing_tgt} missing targets.")

    # [2/3] JUNCTION ANALYSIS
    print("\n[2/3] Analyzing Junction Complexity...")
    with engine.connect() as conn:
        island_query = "SELECT cnt, COUNT(*) as node_count FROM pj_roads_vertices_pgr GROUP BY cnt ORDER BY cnt;"
        rows = conn.execute(text(island_query)).fetchall()
        for row in rows:
            desc = "Dead-end/Cul-de-sac" if row[0] == 1 else f"{row[0]}-way Intersection"
            print(f" - {desc}: {row[1]} nodes")

    # [3/3] RANDOMIZED DIJKSTRA VERIFICATION
    print("\n[3/3] Performing Randomized Pathfinding Test...")
    
    # Selecting two random nodes to ensure different tests on every run
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
                
                # Calculate speed to check for "9.5 hour" anomalies
                avg_speed = (dist_km / (time_sec / 3600)) if time_sec > 0 else 0

                print(f"Dijkstra calculation successful!")
                print(f"-----------------------------------")
                print(f"Path:      Node {start_n} ➔ {end_n}")
                print(f"Distance:  {dist_km:.2f} km")
                print(f"Time:      {round(time_sec, 2)}s ({round(time_sec/60, 2)} mins)")
                print(f"Avg Speed: {round(avg_speed, 2)} km/h")
                print(f"-----------------------------------")
            else:
                print("No path found between these random nodes (Standard for disconnected clusters).")
                print("Hint: Run the script again to test a different pair!")
                
        except Exception as e:
            print(f"Pathfinding logic failed: {e}")

    print("\n--- Sanity Checks Completed ---")

if __name__ == "__main__":
    run_sanity_checks()