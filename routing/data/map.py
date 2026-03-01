"""Fetches road geometries from PostGIS and generates a map visualization of Petaling Jaya."""

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

DB_USER = "postgres"
DB_PASS = "root"
DB_HOST = "localhost"
DB_PORT = "5432"
DB_NAME = "routing_db"

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
ARTIFACTS_DIR = Path(__file__).resolve().parents[1] / "artifacts"


def visualize_full_map():
    """Loads road data from PostGIS and generates a color-coded map image."""
    # Create the connection
    engine = create_engine(DATABASE_URL)

    print(f"Connecting to {DB_NAME}...")

    # Pull the data from PostGIS
    query = "SELECT geometry, highway FROM pj_roads"

    print("Loading road geometries into memory...")
    gdf = gpd.read_postgis(query, engine, geom_col="geometry")

    print(f"Loaded {len(gdf)} road segments.")

    # Create the Visualization
    fig, ax = plt.subplots(figsize=(12, 12))

    print("Rendering map...")

    gdf.plot(
        ax=ax, column="highway", legend=True, linewidth=0.5, alpha=0.8, cmap="tab20b"
    )

    # Final Formatting
    ax.set_title("Full Road Network Extraction: Petaling Jaya", fontsize=15)
    ax.set_axis_off()  # Hide latitude/longitude coordinates for a cleaner look

    # Save the result
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
    output_file = ARTIFACTS_DIR / "pj_full_map_visualization.png"
    plt.savefig(output_file, dpi=300, bbox_inches="tight")

    print(f"Visualization saved as: {output_file}")
    plt.show()


if __name__ == "__main__":
    try:
        visualize_full_map()
    except Exception as e:
        print(f"Error during visualization: {e}")
