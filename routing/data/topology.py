"""Builds the pgRouting topology by creating source/target columns and a vertex table."""

from apps.api.src.app.core.config import get_settings
from sqlalchemy import create_engine, text

# Initialize settings
settings = get_settings()

def build_topology():
    """Sets up the road network topology and generates a junction-aware vertex table."""
    print(f"--- {settings.app_name}: Topology Building ---")
    print(f"Target Environment: {settings.app_env.upper()}")

    # Safely extract host for logging
    db_host = settings.database_url.split('@')[-1]
    print(f"Connecting to: {db_host}")

    engine = create_engine(settings.database_url)

    # Prepare Source/Target Columns
    print("Preparing source and target columns in 'pj_roads'...")
    setup_sql = """
        ALTER TABLE pj_roads ADD COLUMN IF NOT EXISTS source BIGINT;
        ALTER TABLE pj_roads ADD COLUMN IF NOT EXISTS target BIGINT;

        -- Map OSM's 'u' and 'v' columns to pgRouting's expected source/target
        UPDATE pj_roads SET source = u, target = v;

        -- Indexing these speeds up Dijkstra calculations significantly
        CREATE INDEX IF NOT EXISTS pj_roads_source_idx ON pj_roads (source);
        CREATE INDEX IF NOT EXISTS pj_roads_target_idx ON pj_roads (target);
    """

    # Build Vertex Table (Intersections)
    print("Generating 'pj_roads_vertices_pgr' with correct connectivity...")
    manual_vertex_sql = """
        DROP TABLE IF EXISTS pj_roads_vertices_pgr CASCADE;

        CREATE TABLE pj_roads_vertices_pgr AS
        WITH all_nodes AS (
            SELECT source AS node_id FROM pj_roads
            UNION ALL
            SELECT target AS node_id FROM pj_roads
        ),
        counts AS (
            SELECT node_id, COUNT(*) as actual_cnt
            FROM all_nodes
            GROUP BY node_id
        )
        SELECT
            c.node_id AS id,
            c.actual_cnt AS cnt,
            -- Grab the geometry from the start of the road segment
            (SELECT ST_StartPoint(geometry) FROM pj_roads WHERE source = c.node_id LIMIT 1) as the_geom
        FROM counts c;

        ALTER TABLE pj_roads_vertices_pgr ADD PRIMARY KEY (id);
        CREATE INDEX IF NOT EXISTS pj_roads_vertices_geom_idx ON pj_roads_vertices_pgr USING GIST (the_geom);
    """

    with engine.connect() as conn:
        try:
            # Execute the setup and vertex creation
            conn.execute(text(setup_sql))
            conn.execute(text(manual_vertex_sql))
            conn.commit()
            print(f"SUCCESS: Topology rebuilt for {settings.app_env.upper()}.")

            # Connectivity Verification
            check_sql = "SELECT cnt, count(*) FROM pj_roads_vertices_pgr GROUP BY cnt ORDER BY cnt LIMIT 5;"
            res = conn.execute(text(check_sql)).fetchall()

            print("\nConnectivity Summary (Petaling Jaya):")
            for row in res:
                # row[0] is the count of roads meeting at a point, row[1] is how many such points exist
                print(f" - {row[0]}-way connections: {row[1]} nodes")

        except Exception as e:
            conn.rollback()
            print(f"CRITICAL ERROR: Topology generation failed: {e}")

if __name__ == "__main__":
    build_topology()
