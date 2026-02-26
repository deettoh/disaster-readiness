from sqlalchemy import create_engine, text
import time

DATABASE_URL = "postgresql://postgres:root@localhost:5432/routing_db"

def verify_performance():
    engine = create_engine(DATABASE_URL)
    
    # 1. TEST: THE QUERY PLANNER
    # We check if the DB uses the index to find the nearest node to a coordinate
    plan_sql = """
        EXPLAIN ANALYZE
        SELECT id FROM pj_roads_vertices_pgr 
        ORDER BY the_geom <-> ST_SetSRID(ST_Point(101.6, 3.1), 4326) 
        LIMIT 1;
    """

    # 2. TEST: ROUTING SPEED
    # We pick two node IDs (assuming 1 and 100 exist) and run Dijkstra
    routing_sql = """
        SELECT * FROM pgr_dijkstra(
            'SELECT id, source, target, agg_cost AS cost, agg_reverse_cost AS reverse_cost FROM pj_roads',
            (SELECT id FROM pj_roads_vertices_pgr LIMIT 1), 
            (SELECT id FROM pj_roads_vertices_pgr OFFSET 100 LIMIT 1), 
            directed := true
        );
    """

    with engine.connect() as conn:
        print("--- Verification 1: Index Usage Check ---")
        plan_result = conn.execute(text(plan_sql)).fetchall()
        used_index = any("Index Scan" in str(row) or "Index Only Scan" in str(row) for row in plan_result)
        
        if used_index:
            print("SUCCESS: Postgres is actively using your GIST indexes.")
        else:
            print("WARNING: Postgres is performing a Sequential Scan (Indexes ignored).")

        print("\n--- Verification 2: Routing Speed Test ---")
        start_time = time.time()
        route = conn.execute(text(routing_sql)).fetchall()
        end_time = time.time()
        
        duration = (end_time - start_time) * 1000 # Convert to ms
        
        if len(route) > 0:
            print(f"SUCCESS: Route found in {duration:.2f}ms.")
            print(f"(Performance: {'Excellent' if duration < 100 else 'Acceptable' if duration < 500 else 'Slow'})")
        else:
            print("FAILED: Routing query returned no results.")

if __name__ == "__main__":
    verify_performance()