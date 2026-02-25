from sqlalchemy import create_engine, text

# --- CONFIGURATION ---
DATABASE_URL = "postgresql://postgres:root@localhost:5432/routing_db"

def verify_routing_logic():
    engine = create_engine(DATABASE_URL)
    
    with engine.connect() as conn:
        print("--- VERIFYING PGROUTING CONNECTIVITY ---")

        # 1. Pick two actual NON-NULL nodes from your dataset
        # We explicitly filter for NOT NULL to avoid the 'None' subscript error
        nodes_query = text("""
            SELECT 
                (SELECT source FROM pj_roads WHERE source IS NOT NULL LIMIT 1) as start_node,
                (SELECT target FROM pj_roads WHERE target IS NOT NULL OFFSET 100 LIMIT 1) as end_node
        """)
        
        result = conn.execute(nodes_query).fetchone()
        
        # Safety check: ensure result and its elements exist
        if result is None or result[0] is None or result[1] is None:
            print("❌ ERROR: Could not find valid source/target nodes. Is the table empty?")
            return
            
        start_node = result[0]
        end_node = result[1]
        
        print(f"Attempting to route from Node {start_node} to Node {end_node}...")

        # 2. Run pgr_dijkstra
        # Using directed := false to allow two-way travel on all roads for this test
        query = text(f"""
            SELECT * FROM pgr_dijkstra(
                'SELECT id, source, target, cost FROM pj_roads',
                {start_node}, 
                {end_node}, 
                false
            );
        """)

        try:
            path = conn.execute(query).fetchall()
            
            if path and len(path) > 0:
                total_cost = sum(row.cost for row in path if row.cost is not None)
                print(f"\n✅ SUCCESS!")
                print(f"Path found! It took {len(path)} road segments.")
                print(f"Total distance (cost): {round(total_cost, 2)} units.")
            else:
                print("\n❌ FAILED: No path found between those two specific nodes.")
                
        except Exception as e:
            print(f"\n❌ ERROR during routing execution: {e}")

if __name__ == "__main__":
    verify_routing_logic()