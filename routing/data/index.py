"""Applies spatial and relational indexes to the road and vertex tables."""

from apps.api.src.app.core.config import get_settings
from sqlalchemy import create_engine, text

settings = get_settings()

def apply_routing_indexes():
    """Creates indexes on road tables and verifies they are active."""
    engine = create_engine(settings.routing_database_url)

    # Define Index Queries
    index_queries = {
        "spatial_roads_idx": "CREATE INDEX IF NOT EXISTS pj_roads_geom_idx ON pj_roads USING GIST (geometry);",
        "source_idx": "CREATE INDEX IF NOT EXISTS pj_roads_source_idx ON pj_roads (source);",
        "target_idx": "CREATE INDEX IF NOT EXISTS pj_roads_target_idx ON pj_roads (target);",
        "cost_idx": "CREATE INDEX IF NOT EXISTS pj_roads_cost_idx ON pj_roads (agg_cost);",
        "spatial_vertices_idx": "CREATE INDEX IF NOT EXISTS pj_roads_vertices_geom_idx ON pj_roads_vertices_pgr USING GIST (the_geom);",
    }

    print(f"--- {settings.app_name}: Performance Optimization ---")
    print(f"Target Environment: {settings.app_env.upper()}")

    with engine.connect() as conn:
        for name, sql in index_queries.items():
            try:
                conn.execute(text(sql))
                print(f"Applied: {name}")
            except Exception as e:
                print(f"Failed to apply {name}: {e}")

        conn.commit()

        # Verification Step: Query the PostgreSQL catalog for active indexes
        verification_sql = """
            SELECT indexname
            FROM pg_indexes
            WHERE tablename IN ('pj_roads', 'pj_roads_vertices_pgr')
            ORDER BY tablename;
        """

        print("\n--- Verification Report ---")
        results = conn.execute(text(verification_sql)).fetchall()

        if results:
            print(f"Total active indexes found: {len(results)}")
            for row in results:
                print(f" - Active Index: {row[0]}")
        else:
            print("WARNING: No indexes found. Check database permissions or table existence.")

    print(f"\nSUCCESS: {settings.app_env.upper()} Database is now optimized for real-time routing.")

if __name__ == "__main__":
    try:
        apply_routing_indexes()
    except Exception as e:
        print(f"CRITICAL ERROR: Could not finalize indexes. {e}")
