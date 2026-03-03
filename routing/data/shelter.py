"""Prepare a shelter location file."""

import warnings
from pathlib import Path

import osmnx as ox
import pandas as pd
from apps.api.src.app.core.config import get_settings

# Initialize settings
settings = get_settings()

# Ignore the CRS warning for centroids
warnings.filterwarnings("ignore", category=UserWarning)

# Define Artifacts directory relative to the project root
ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"


def download_safe_shelters():
    """Downloads PJ community centers likely used for flood/disaster relief."""
    # 0. Infrastructure Check & Environment Prompt
    print(f"--- {settings.app_name}: Shelter Data Acquisition ---")
    print(f"Target Environment: {settings.app_env.upper()}")

    place_name = "Petaling Jaya, Selangor, Malaysia"

    # Refined tags: Community centers and halls are the standard 'safe' zones in PJ
    tags: dict[str, str | bool | list[str]] = {
        "amenity": ["community_centre", "townhall"],
        "building": "civic",
    }

    print(f"Fetching safe evacuation centers for {place_name} from OSM...")

    try:
        # Get features from OSM
        shelters = ox.features_from_place(place_name, tags)

        if shelters.empty:
            print(f"Warning: No shelters found for {settings.app_env.upper()} criteria.")
            return

        # Project to meters for accurate center point calculation, then back to GPS
        shelters_proj = ox.projection.project_gdf(shelters)
        points = shelters_proj.centroid.to_crs(epsg=4326)

        # Extract names (fallback if name is missing)
        if "name" in shelters.columns:
            names = shelters["name"].fillna("Dewan Komuniti (Unspecified)")
        else:
            names = ["Dewan Komuniti"] * len(shelters)

        # Create Clean DataFrame
        df = pd.DataFrame({
            'name': names,
            'lon': points.x,
            'lat': points.y
        })

        # Safety Filter: Prioritize "Dewan" or "Pusat Komuniti" (Local naming conventions)
        df = df[df['name'].str.contains('Dewan|Pusat|Komuniti|Hall', case=False, na=False)]

        # We take the top 5 most relevant for the MVP/Scenario testing
        df = df.head(5).reset_index(drop=True)

        # Export to Artifacts folder
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        output_file = ARTIFACTS_DIR / "pj_shelters.csv"

        df.to_csv(output_file, index_label="shelter_id")

        print(f"\nSUCCESS: Saved {len(df)} SAFE shelters to '{output_file}'")
        print(f"Environment Artifacts: {ARTIFACTS_DIR}")
        print("-" * 60)
        print(df[["name", "lon", "lat"]].to_string())
        print("-" * 60)

    except Exception as e:
        print(f"CRITICAL ERROR fetching shelters: {e}")


if __name__ == "__main__":
    download_safe_shelters()
