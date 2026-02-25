from sqlalchemy import create_engine, text

# --- CONFIGURATION ---
DATABASE_URL = "postgresql://postgres:root@localhost:5432/routing_db"

def build_topology():
    engine = create_engine(DATABASE_URL)
    
    # 1. Clean up old data
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS pj_roads_vertices_pgr;"))
        conn.commit()

    # 2. Assign Source and Target from OSM IDs (The core mapping)
    print("Mapping source and target columns...")
    with engine.connect() as conn:
        conn.execute(text("ALTER TABLE pj_roads ADD COLUMN IF NOT EXISTS source BIGINT;"))
        conn.execute(text("ALTER TABLE pj_roads ADD COLUMN IF NOT EXISTS target BIGINT;"))
        conn.execute(text("UPDATE pj_roads SET source = u, target = v;"))
        conn.commit()

    # 3. Build Vertex Table Manually (The Manual Fallback)
    # This creates the list of unique nodes and their locations
    print("Generating pj_roads_vertices_pgr manually...")
    manual_vertex_sql = """
        CREATE TABLE pj_roads_vertices_pgr AS
        WITH all_nodes AS (
            SELECT source as node_id, ST_StartPoint(geometry) as geom FROM pj_roads
            UNION
            SELECT target as node_id, ST_EndPoint(geometry) as geom FROM pj_roads
        )
        SELECT 
            node_id as id, 
            ST_Centroid(ST_Collect(geom)) as the_geom,
            count(*) as cnt
        FROM all_nodes
        GROUP BY node_id;
    """
    
    with engine.connect() as conn:
        try:
            conn.execute(text(manual_vertex_sql))
            conn.execute(text("ALTER TABLE pj_roads_vertices_pgr ADD PRIMARY KEY (id);"))
            conn.commit()
            print("✅ Vertex table created manually from OSM nodes.")
        except Exception as e:
            print(f"❌ Manual creation failed: {e}")

    # 4. Verification
    with engine.connect() as conn:
        res = conn.execute(text("SELECT count(*) FROM pj_roads_vertices_pgr;")).fetchone()
        if res:
            print(f"\nSUCCESS! Found {res[0]} unique intersections (nodes).")

if __name__ == "__main__":
    build_topology()