"""Downloads Petaling Jaya road networks and imports them into a PostGIS database for pgRouting."""

import geopandas as gpd
import osmnx as ox
from apps.api.src.app.core.config import get_settings
from sqlalchemy import create_engine, text

settings = get_settings()

def import_roads():
    """Downloads PJ road data and uploads it to a PostGIS database for routing."""
    print(f"--- {settings.app_name}: Database Loading & Initialization ---")
    print(f"Target Environment: {settings.app_env.upper()}")

    # Safely extract host for logging
    db_host = settings.database_url.split('@')[-1]
    print(f"Connecting to: {db_host}")

    engine = create_engine(settings.database_url)

    # Initialize extensions
    with engine.connect() as conn:
        print("Enabling PostGIS and pgRouting extensions...")
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS pgrouting;"))
        conn.commit()

    # Fetch road data from OpenStreetMap
    place_name = "Petaling Jaya, Selangor, Malaysia"
    print(f"Fetching road network for: {place_name}...")

    # network_type='drive' ensures we only get roads suitable for vehicles
    graph = ox.graph_from_place(place_name, network_type="drive")

    # Process data into GeoDataFrames
    _, edges = ox.graph_to_gdfs(graph)
    edges = edges.reset_index()

    # Prepare standard columns for pgRouting
    print("Preparing columns for routing logic...")
    edges = gpd.GeoDataFrame(edges, geometry="geometry")
    edges["id"] = range(1, len(edges) + 1)

    # Initial cost is usually the length of the segment (meters)
    edges["cost"] = edges["length"]

    # Clean up OSM list types (Postgres columns cannot store Python lists natively)
    for col in edges.columns:
        if edges[col].apply(lambda x: isinstance(x, list)).any():
            edges[col] = edges[col].astype(str)

    # Upload to PostGIS
    print("Uploading edges to table 'pj_roads'...")
    edges.to_postgis("pj_roads", engine, if_exists="replace", index=False)

    # Create Spatial Index
    with engine.connect() as conn:
        print("Creating spatial GIST index for performance...")
        conn.execute(
            text(
                "CREATE INDEX IF NOT EXISTS pj_roads_geom_idx ON pj_roads USING GIST (geometry);"
            )
        )
        conn.commit()

    print(f"SUCCESS: {len(edges)} road segments imported into 'pj_roads' table in {settings.app_env.upper()}.")


if __name__ == "__main__":
    try:
        import_roads()
    except Exception as e:
        print(f"CRITICAL ERROR: Import failed. Details: {e}")
