from sqlalchemy import create_engine, text

engine = create_engine('postgresql://postgres:root@localhost:5432/routing_db')

def perform_routability_test():
    print("🛰️ Connecting to routing_db for a live path test...")
    
    with engine.connect() as conn:
        # We specify pj_roads.cost to remove the ambiguity
        test_query = text("""
            SELECT sum(pj_roads.cost) as total_meters 
            FROM pgr_dijkstra(
                'SELECT id, source, target, cost FROM pj_roads',
                (SELECT source FROM pj_roads LIMIT 1), 
                (SELECT target FROM pj_roads OFFSET 100 LIMIT 1),
                false
            ) as path
            JOIN pj_roads ON path.edge = pj_roads.id;
        """)
        
        result = conn.execute(test_query).scalar()
        
        if result:
            print(f"✅ SUCCESS! The engine found a path.")
            print(f"📏 Total travel distance: {round(result, 2)} meters.")
        else:
            # If result is None, it means A and B aren't connected
            print("❌ FAIL: No path found between those two points.")

if __name__ == "__main__":
    perform_routability_test()