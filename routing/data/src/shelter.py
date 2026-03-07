"""Prepare a shelter location file and seed the shelter table in Supabase."""

import os
import sys
import warnings  # noqa: D100
from pathlib import Path

# Add project root and API source to python path
sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
)
sys.path.append(
    os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "..", "apps", "api", "src")
    )
)

import geopandas as gpd
import osmnx as ox
from sqlalchemy import create_engine

from app.core.config import get_settings

# Ignore the CRS warning for centroids
warnings.filterwarnings("ignore", category=UserWarning)

# Define project-relative paths
BASE_DIR = Path(__file__).resolve().parents[3]
ARTIFACTS_DIR = BASE_DIR / "routing" / "artifacts"


def download_safe_shelters():
    """Fetch community centers from OpenStreetMap and upload them to the spatial database."""
    settings = get_settings()
    print(f"--- {settings.app_name}: Shelter Data Acquisition ---")

    # --- STEP 1: Fetch from OSM ---
    place_name = "Petaling Jaya, Selangor, Malaysia"
    tags = {
        "amenity": ["community_centre", "townhall"],
        "building": "civic",
    }

    print(f"Fetching safe evacuation centers for {place_name} from OSM...")

    try:
        shelters = ox.features_from_place(place_name, tags)

        if shelters.empty:
            print("Warning: No shelters found.")
            return

        # Project to calculate centroids correctly
        shelters_proj = ox.projection.project_gdf(shelters)
        points = shelters_proj.centroid.to_crs(epsg=4326)

        # Extract names
        names = (
            shelters["name"].fillna("Dewan Komuniti (Unspecified)")
            if "name" in shelters.columns
            else ["Dewan Komuniti"] * len(shelters)
        )

        # Create GeoDataFrame for Spatial Upload
        gdf = gpd.GeoDataFrame(
            {"name": names, "capacity": 0, "geometry": points}, crs="EPSG:4326"
        )

        # Local naming filter
        gdf = gdf[
            gdf["name"].str.contains("Dewan|Pusat|Komuniti|Hall", case=False, na=False)
        ]

        # Take top 5 for MVP
        gdf = gdf.head(5).reset_index(drop=True)
        gdf.index.name = "id"

        # Save Local CSV (Backup) - specifically formatted for frontend's shelterCSVToGeoJSON
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        output_file = ARTIFACTS_DIR / "pj_shelters.csv"

        # Prepare CSV output with split lat/lon for easy frontend parsing
        csv_df = gdf.copy()
        csv_df["lat"] = gdf.geometry.y
        csv_df["lon"] = gdf.geometry.x
        csv_df = csv_df.drop(columns=["geometry"])
        csv_df.to_csv(output_file, index=True, index_label="shelter_id")

        # Upload to Supabase
        db_url = settings.database_url
        if not db_url or "YOUR_PROJECT_REF" in db_url:
            db_url = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"

        print(f"Uploading shelters to database at {db_url.split('@')[-1]}...")
        engine = create_engine(db_url)

        # Upload to 'shelters' table in 'public' schema
        gdf.to_postgis(
            "shelters", engine, schema="public", if_exists="replace", index=True
        )

        print(f"\nSUCCESS: Seeded {len(gdf)} shelters to database and '{output_file}'")
        print("-" * 60)
        print(gdf[["name"]].to_string())
        print("-" * 60)

    except Exception as e:
        print(f"CRITICAL ERROR seeding shelters: {e}")


if __name__ == "__main__":
    download_safe_shelters()
