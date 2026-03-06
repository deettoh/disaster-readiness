"""Fetches road geometries from PostGIS and generates a map visualization of Petaling Jaya."""

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from apps.api.src.app.core.config import get_settings
from sqlalchemy import create_engine

# Initialize settings
settings = get_settings()

# Define Artifacts directory relative to this file
ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"


def visualize_full_map():
    """Loads road data from PostGIS and generates a color-coded map image."""
    print(f"--- {settings.app_name}: Map Visualization ---")
    print(f"Target Environment: {settings.app_env.upper()}")

    # Safely extract host for logging (don't print password)
    db_host = settings.database_url.split('@')[-1]
    print(f"Connecting to: {db_host}")

    # Use the database URL from centralized settings
    engine = create_engine(settings.database_url)

    # Pull the data from PostGIS
    query = "SELECT geometry, highway FROM pj_roads"

    try:
        print("Loading road geometries into memory (GeoPandas)...")
        gdf = gpd.read_postgis(query, engine, geom_col="geometry")

        if gdf.empty:
            print(f"Warning: No data found in 'pj_roads' for {settings.app_env.upper()}. Did you run load_postgres.py?")
            return

        print(f"Loaded {len(gdf)} road segments.")

        # Create the Visualization
        fig, ax = plt.subplots(figsize=(12, 12))

        print("Rendering map...")

        # Plotting with categorization based on road type (highway)
        gdf.plot(
            ax=ax,
            column='highway',
            legend=True,
            linewidth=0.5,
            alpha=0.8,
            cmap='tab20b',
            legend_kwds={'loc': 'upper left', 'bbox_to_anchor': (1, 1), 'fontsize': 'small'}
        )

        # Final Formatting
        ax.set_title(f"Road Network: Petaling Jaya ({settings.app_env.upper()})", fontsize=15)
        ax.set_axis_off()

        # Ensure artifacts directory exists
        ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
        output_path = ARTIFACTS_DIR / "pj_full_map_visualization.png"

        # Save the result
        plt.savefig(output_path, dpi=300, bbox_inches='tight')
        print(f"SUCCESS: Visualization saved as: {output_path}")

        # Display if running in an interactive environment (e.g., Jupyter)
        # plt.show()

    except Exception as e:
        print(f"CRITICAL ERROR: Database/Visualization failed: {e}")

if __name__ == "__main__":
    visualize_full_map()
