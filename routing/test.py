import sqlalchemy
from sqlalchemy import create_engine, text

DB_URL = "postgresql://postgres:root@localhost:5432/routing_db"

def validate_routing_graph():
    engine = create_engine(DB_URL)
    
    with engine.connect() as conn:
        print("🔍 Starting Graph Validation Suite...\n")
        
        # --- 1. INTEGRITY CHECK: MATH & LOGIC ---
        integrity_sql = """
            SELECT 
                COUNT(*) FILTER (WHERE ABS(agg_cost - (base_cost + risk_penalty)) > 0.001) as math_errors,
                COUNT(*) FILTER (WHERE oneway IN ('yes', 'true', '1') AND agg_reverse_cost != -1) as oneway_errors,
                COUNT(*) FILTER (WHERE agg_cost <= 0) as zero_cost_errors,
                COUNT(*) FILTER (WHERE risk_penalty IS NULL) as null_risk_errors
            FROM pj_roads;
        """
        
        try:
            res = conn.execute(text(integrity_sql)).fetchone()
            
            # Defensive check: Only try to subscript if res is NOT None
            if res is not None:
                math_err = res[0] if res[0] is not None else 0
                ow_err   = res[1] if res[1] is not None else 0
                zero_err = res[2] if res[2] is not None else 0
                null_err = res[3] if res[3] is not None else 0
            else:
                # Fallback defaults if the query returned nothing
                math_err = ow_err = zero_err = null_err = 0

            print("--- [1] Logic & Integrity Check ---")
            print(f"{'Success' if math_err == 0 else 'Error'} Math Consistency: {math_err} errors")
            print(f"{'Success' if ow_err == 0 else 'Error'} One-Way Logic: {ow_err} errors")
            print(f"{'Success' if zero_err == 0 else 'Error'} Zero/Negative Costs: {zero_err} errors")
            print(f"{'Success' if null_err == 0 else 'Error'} Task 5 (Risk Init): {null_err} nulls")
        
        except Exception as e:
            print(f"Integrity Query Failed: {e}")

        # --- 2. SAMPLE AUDIT ---
        print("\n--- [2] Data Sample Audit ---")
        try:
            samples = conn.execute(text("""
                SELECT COALESCE(name, 'Unnamed Road'), highway, 
                       round(base_cost::numeric, 2), risk_penalty, round(agg_cost::numeric, 2)
                FROM pj_roads 
                WHERE base_cost IS NOT NULL 
                LIMIT 5;
            """)).fetchall()
            
            if not samples:
                print("⚠️ No road samples found. Check if pj_roads table has data.")
            else:
                for s in samples:
                    print(f" • {s[0]} ({s[1]}): Base {s[2]}s + Risk {s[3]} = Total {s[4]}s")
        except Exception as e:
            print(f"Sample Audit Failed: {e}")

        # --- 3. FUNCTIONAL TEST: PGROUTING DIJKSTRA ---
        print("\n--- [3] Functional Connectivity Test ---")
        try:
            nodes_res = conn.execute(text("SELECT id FROM pj_roads_vertices_pgr LIMIT 2;")).fetchall()
            
            if not nodes_res or len(nodes_res) < 2:
                print("Not enough nodes found in pj_roads_vertices_pgr to test routing.")
            else:
                start_id = nodes_res[0][0]
                end_id = nodes_res[1][0]
                
                pgr_sql = f"""
                    SELECT seq, node, edge, cost 
                    FROM pgr_dijkstra(
                        'SELECT id, source, target, agg_cost AS cost, agg_reverse_cost AS reverse_cost FROM pj_roads',
                        {start_id}, {end_id}, directed := true
                    );
                """
                route = conn.execute(text(pgr_sql)).fetchall()
                
                if route:
                    print(f"Success! pgRouting found a path between Node {start_id} and {end_id}.")
                    print(f"Path Length: {len(route)} segments.")
                else:
                    print(f"Path not found between {start_id} and {end_id}. (Roads might be disconnected).")

        except Exception as e:
            print(f"pgRouting Test Failed: {e}")

if __name__ == "__main__":
    validate_routing_graph()