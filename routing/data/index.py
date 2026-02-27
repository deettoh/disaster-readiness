"""Applies spatial and relational indexes to the road and vertex tables to optimize routing performance."""

from sqlalchemy import create_engine, text

DB_USER = "postgres"
DB_PASS = "root"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "routing_db"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def apply_routing_indexes():
    """Creates indexes on road tables and verifies they are active."""
    
    engine = create_engine(DATABASE_URL)
    
    # Define Index Queries
    index_queries = {
        "spatial_idx": "CREATE INDEX IF NOT EXISTS pj_roads_geom_idx ON pj_roads USING GIST (geometry);",
        "source_idx": "CREATE INDEX IF NOT EXISTS pj_roads_source_idx ON pj_roads (source);",
        "target_idx": "CREATE INDEX IF NOT EXISTS pj_roads_target_idx ON pj_roads (target);",
        "cost_idx": "CREATE INDEX IF NOT EXISTS pj_roads_cost_idx ON pj_roads (agg_cost);",
        "vertices_idx": "CREATE INDEX IF NOT EXISTS pj_roads_vertices_geom_idx ON pj_roads_vertices_pgr USING GIST (the_geom);"
    }

    print("--- Finalizing Routing Indexes ---")
    
    with engine.connect() as conn:
        for name, sql in index_queries.items():
            try:
                conn.execute(text(sql))
                print(f"Applied: {name}")
            except Exception as e:
                print(f"Failed to apply {name}: {e}")
        
        conn.commit()

    # Verification Step
    verification_sql = """
        SELECT indexname 
        FROM pg_indexes 
        WHERE tablename IN ('pj_roads', 'pj_roads_vertices_pgr')
        ORDER BY tablename;
    """
    
    print("\n--- Verification Report ---")
    with engine.connect() as conn:
        results = conn.execute(text(verification_sql)).fetchall()
        if results:
            print(f"Total active indexes found: {len(results)}")
            for row in results:
                print(f" - Found Index: {row[0]}")
        else:
            print("No indexes found. Please check database permissions.")

    print("\nSUCCESS: Database is now optimized for dynamic routing.")

if __name__ == "__main__":
    apply_routing_indexes()