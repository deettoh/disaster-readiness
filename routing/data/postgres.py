"""Downloads Petaling Jaya road networks and imports them into a PostGIS database for pgRouting."""

import osmnx as ox
from sqlalchemy import create_engine, text
import geopandas as gpd

DB_USER = "postgres"
DB_PASS = "root"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "routing_db"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def import_roads():
    """Downloads PJ road data and uploads it to a PostGIS database for routing."""
    
    engine = create_engine(DATABASE_URL)
    
    # Initialize extensions
    with engine.connect() as conn:
        print("Enabling PostGIS and pgRouting...")
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgrouting;"))
        conn.commit()

    # Fetch road data
    place_name = "Petaling Jaya, Selangor, Malaysia"
    print(f"Fetching graph for {place_name}...")
    graph = ox.graph_from_place(place_name, network_type='drive')
    
    # Process data
    nodes, edges = ox.graph_to_gdfs(graph)
    edges = edges.reset_index()
    
    edges = gpd.GeoDataFrame(edges, geometry='geometry')
    
    # Prepare standard columns
    edges['id'] = range(1, len(edges) + 1)
    edges['cost'] = edges['length']
    
    # Clean up OSM list types 
    for col in edges.columns:
        if edges[col].apply(lambda x: isinstance(x, list)).any():
            edges[col] = edges[col].astype(str)

    # Upload to PostGIS
    print("Uploading edges to PostGIS...")
    edges.to_postgis('pj_roads', engine, if_exists='replace', index=False)
    
    with engine.connect() as conn:
        conn.execute(text("CREATE INDEX IF NOT EXISTS pj_roads_geom_idx ON pj_roads USING GIST (geometry);"))
        conn.commit()
        
    print("SUCCESS: Roads imported into 'pj_roads' table.")

if __name__ == "__main__":
    import_roads()

