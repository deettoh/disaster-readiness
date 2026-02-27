from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:root@localhost:5432/routing_db"

def build_topology():
    """Sets up the road network topology and generates a junction-aware vertex table."""
    
    engine = create_engine(DATABASE_URL)
    
    # Prepare Columns
    print("Preparing source and target columns...")
    setup_sql = """
        ALTER TABLE pj_roads ADD COLUMN IF NOT EXISTS source BIGINT;
        ALTER TABLE pj_roads ADD COLUMN IF NOT EXISTS target BIGINT;
        UPDATE pj_roads SET source = u, target = v;
    """

    # Build Vertex Table 
    print("Generating pj_roads_vertices_pgr with correct connectivity...")
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
            (SELECT ST_StartPoint(geometry) FROM pj_roads WHERE source = c.node_id LIMIT 1) as the_geom
        FROM counts c;
        
        ALTER TABLE pj_roads_vertices_pgr ADD PRIMARY KEY (id);
        CREATE INDEX IF NOT EXISTS pj_roads_vertices_geom_idx ON pj_roads_vertices_pgr USING GIST (the_geom);
    """
    
    with engine.connect() as conn:
        try:
            conn.execute(text(setup_sql))
            conn.execute(text(manual_vertex_sql))
            conn.commit()
            print("SUCCESS: Topology rebuilt with correct junction counts.")
            
            # Verification
            res = conn.execute(text("SELECT cnt, count(*) FROM pj_roads_vertices_pgr GROUP BY cnt ORDER BY cnt LIMIT 5;")).fetchall()
            print("\nConnectivity Summary:")
            for row in res:
                print(f" - {row[0]}-way connections: {row[1]} nodes")
                
        except Exception as e:
            conn.rollback()
            print(f"FAILED: {e}")

if __name__ == "__main__":
    build_topology()