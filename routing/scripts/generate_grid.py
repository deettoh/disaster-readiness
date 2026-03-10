"""Generate a 500m x 500m spatial grid for Petaling Jaya and upload to Supabase."""

import argparse
import os
import sys

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, ROOT_DIR)
sys.path.insert(0, os.path.join(ROOT_DIR, "apps", "api", "src"))

import geopandas as gpd  # noqa: E402
import numpy as np  # noqa: E402
from dotenv import load_dotenv  # noqa: E402
from shapely.geometry import Polygon  # noqa: E402
from sqlalchemy import create_engine, text  # noqa: E402

from app.core.config import get_settings  # noqa: E402

load_dotenv(os.path.join(ROOT_DIR, ".env"))


def run_grid_generation():
    """Generate a 500m x 500m spatial grid for Petaling Jaya and upload to Supabase."""
    parser = argparse.ArgumentParser(description="Generate 500m grid for PJ")
    parser.add_argument("--db-url", help="Override the DATABASE_URL")
    args = parser.parse_args()

    # Prioritize provided argument, then Settings
    if args.db_url:
        db_url = args.db_url
    else:
        try:
            settings = get_settings()
            db_url = settings.database_url
            if not db_url or "YOUR_PROJECT_REF" in db_url:
                db_url = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
        except Exception:
            db_url = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"

    print(f"Connecting to Database: {db_url.split('@')[-1]}")

    # 1. Load local PJ Boundary (for clipping) and Neighborhoods (for labeling)
    boundary_path = os.path.join(ROOT_DIR, "routing/data/pj_boundary.geojson")
    neighbourhood_path = os.path.join(ROOT_DIR, "routing/data/pj_neighbourhood.geojson")

    if not os.path.exists(boundary_path):
        print(f"Error: Boundary file not found at {boundary_path}")
        return
    if not os.path.exists(neighbourhood_path):
        print(f"Error: Neighbourhood file not found at {neighbourhood_path}")
        return

    print("Loading geographic files...")
    boundary = gpd.read_file(boundary_path)
    all_features_gdf = gpd.read_file(neighbourhood_path)

    # Filter for specific neighborhoods (admin_level == 10)
    # This avoids tagging everything as the city-wide "Petaling Jaya" polygon
    print("Filtering and processing neighborhood features...")
    neighbourhoods_gdf = all_features_gdf[
        (all_features_gdf["admin_level"].fillna("10").astype(int) == 10)
        & (all_features_gdf["name"].notna())
    ].copy()

    # Project to Malaysia-specific metric CRS (EPSG:3168) for accurate 500m math
    boundary = boundary.to_crs(epsg=3168)
    neighbourhoods_gdf = neighbourhoods_gdf.to_crs(epsg=3168)

    # 2. Generate 500m x 500m Grid
    print("Generating 500m grid...")
    xmin, ymin, xmax, ymax = boundary.total_bounds
    rows = int(np.ceil((ymax - ymin) / 500))
    cols = int(np.ceil((xmax - xmin) / 500))

    grid_cells = []
    for i in range(cols):
        for j in range(rows):
            x1 = xmin + i * 500
            y1 = ymin + j * 500
            x2 = x1 + 500
            y2 = y1 + 500
            grid_cells.append(Polygon([(x1, y1), (x2, y1), (x2, y2), (x1, y2)]))

    grid = gpd.GeoDataFrame({"geometry": grid_cells}, crs=3168)

    # 3. Clip and Label
    print("Clipping grid to PJ boundary...")
    grid_pj = gpd.clip(grid, boundary)

    print("Performing spatial join with neighborhoods...")
    grid_pj = gpd.sjoin(
        grid_pj,
        neighbourhoods_gdf[["name", "geometry"]],
        how="left",
        predicate="intersects",
    )

    # Resolve cells matching multiple neighborhoods
    grid_pj = grid_pj.groupby(grid_pj.index).first()

    # Force assign at least one cell for every neighborhood in the source data.
    print("Verifying 100% neighborhood coverage...")
    all_names = set(neighbourhoods_gdf["name"].unique())
    assigned_names = set(grid_pj["name"].dropna().unique())
    missing_names = all_names - assigned_names

    if missing_names:
        print(
            f"  Found {len(missing_names)} missing neighborhoods. Forcing assignment..."
        )
        # Project grid to same CRS for matching
        grid_metric = gpd.GeoDataFrame(grid_pj, geometry="geometry", crs=3168)

        for name in missing_names:
            poly = neighbourhoods_gdf[neighbourhoods_gdf["name"] == name].geometry.iloc[
                0
            ]
            matches = grid_metric[grid_metric.geometry.intersects(poly)]
            if not matches.empty:
                target_idx = matches.index[0]
                grid_pj.at[target_idx, "name"] = name
                print(f"    Forcing Cell {target_idx} -> '{name}'")
            else:
                print(f"    Warning: No grid cells found for '{name}'")

    # Explicitly restore GeoDataFrame with CRS
    grid_pj = gpd.GeoDataFrame(grid_pj, geometry="geometry", crs=3168)

    # Project back to standard GPS coordinates (WGS84)
    grid_pj = grid_pj.to_crs(epsg=4326)
    grid_pj.index.name = "id"

    grid_pj = grid_pj.rename(columns={"name": "neighborhood"})
    grid_pj["neighborhood"] = grid_pj["neighborhood"].fillna(
        "Petaling Jaya (Unclassified)"
    )

    # 4. Upload to PostGIS
    engine = create_engine(db_url)

    print("Syncing neighborhoods table and grid data...")
    with engine.connect() as conn:
        conn.execute(text("TRUNCATE TABLE public.grid_cells CASCADE;"))
        conn.execute(text("TRUNCATE TABLE public.neighborhoods CASCADE;"))
        conn.commit()

    grid_pj = grid_pj.rename_geometry("geom")

    print(f"Uploading {len(grid_pj)} grid cells...")
    grid_pj[["geom", "neighborhood"]].to_postgis(
        "grid_cells", engine, schema="public", if_exists="append", index=True
    )

    print("Seeding neighborhoods table from source file...")
    # Extract unique neighborhoods from the source file
    cols_to_extract = ["name"]
    if "postal_code" in neighbourhoods_gdf.columns:
        cols_to_extract.append("postal_code")

    unique_neighborhoods = (
        neighbourhoods_gdf[cols_to_extract].drop_duplicates("name").copy()
    )
    if "postal_code" in unique_neighborhoods.columns:
        unique_neighborhoods = unique_neighborhoods.rename(
            columns={"postal_code": "code"}
        )
    else:
        unique_neighborhoods["code"] = None

    unique_neighborhoods["description"] = (
        "Neighborhood defined in OSM Petaling Jaya data"
    )

    unique_neighborhoods.to_sql(
        "neighborhoods", engine, schema="public", if_exists="append", index=False
    )

    print(f"SUCCESS: {len(unique_neighborhoods)} neighborhoods and Grid uploaded.")


if __name__ == "__main__":
    run_grid_generation()
