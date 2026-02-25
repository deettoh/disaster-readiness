import osmnx as ox
from sqlalchemy import create_engine, text
import geopandas as gpd

# --- 1. CONFIGURATION ---
DB_USER = "postgres"
DB_PASS = "root"  
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "routing_db"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def setup_routing_db_bypass():
    engine = create_engine(DATABASE_URL)
    
    # --- STEP A: INITIALIZE EXTENSIONS ---
    with engine.connect() as conn:
        print("🌍 Enabling PostGIS and pgRouting...")
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgrouting;"))
        conn.commit()

    # --- STEP B: FETCH ROAD DATA ---
    place_name = "Petaling Jaya, Selangor, Malaysia"
    print(f"🛰️  Fetching graph for {place_name}...")
    graph = ox.graph_from_place(place_name, network_type='drive')
    
    # --- STEP C: PROCESS DATA ---
    # OSMNX gives us 'u' and 'v' which are the start and end point IDs
    nodes, edges = ox.graph_to_gdfs(graph)
    edges = edges.reset_index()
    
    # 1. Create a unique ID for every edge
    edges['id'] = range(1, len(edges) + 1)
    
    # 2. Map OSM nodes (u, v) to pgRouting columns (source, target)
    # We use the actual OSM Node IDs. They are BigInts.
    edges['source'] = edges['u']
    edges['target'] = edges['v']
    
    # 3. Rename 'length' to 'cost' for easier routing queries
    if 'length' in edges.columns:
        edges['cost'] = edges['length']
    else:
        edges['cost'] = 1.0 # fallback

    # 4. Clean up OSM list types
    for col in edges.columns:
        if edges[col].apply(lambda x: isinstance(x, list)).any():
            edges[col] = edges[col].astype(str)

    # --- STEP D: UPLOAD TO POSTGIS ---
    print("🚀 Uploading edges to PostGIS...")
    edges.to_postgis('pj_roads', engine, if_exists='replace', index=False)

    # --- STEP E: MANUAL TOPOLOGY SETUP ---
    # Instead of calling pgr_createTopology, we manually index the columns
    print("🧬 Finalizing network indexing...")
    with engine.connect() as conn:
        # Create indexes to make routing fast
        conn.execute(text("CREATE INDEX IF NOT EXISTS pj_roads_source_idx ON pj_roads(source);"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS pj_roads_target_idx ON pj_roads(target);"))
        conn.commit()
        
        # --- TEST ROUTE ---
        # Let's try to run a simple Dijkstra to prove it works!
        print("🧪 Testing Dijkstra on the new graph...")
        test_query = text("""
            SELECT * FROM pgr_dijkstra(
                'SELECT id, source, target, cost FROM pj_roads',
                (SELECT source FROM pj_roads LIMIT 1), 
                (SELECT target FROM pj_roads OFFSET 10 LIMIT 1),
                false
            );
        """)
        result = conn.execute(test_query).fetchone()
        
    if result:
        print("\n🎉 SUCCESS! pgRouting is working using OSM-native topology.")
        print("You bypassed the missing pgr_createTopology function successfully.")
    else:
        print("\n⚠️ Data uploaded, but test route failed. Check node connections.")

    return engine

if __name__ == "__main__":
    try:
        setup_routing_db_bypass()
    except Exception as e:
        print(f"\nFATAL ERROR: {e}")

