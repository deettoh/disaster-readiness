"""Visualizes the risk imputation results on a map of Petaling Jaya."""

import os
from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
from dotenv import load_dotenv
from sqlalchemy import create_engine

PROJECT_ROOT = Path(__file__).resolve().parents[3]
load_dotenv(PROJECT_ROOT / ".env")


def visualize():
    """Fetches grid cells with scores from DB and saves a choropleth map."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not set in environment.")
        return
    engine = create_engine(db_url)

    ARTIFACTS_DIR = PROJECT_ROOT / "ai" / "imputation" / "artifacts"
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    print("Loading grid cells and vulnerability scores from Database...")
    query = "SELECT id, geom, baseline_vulnerability FROM grid_cells WHERE baseline_vulnerability IS NOT NULL"

    try:
        gdf = gpd.read_postgis(query, engine, geom_col="geom")

        if gdf.empty:
            print(
                "No data found in grid_cells with baseline_vulnerability. Run writeback first."
            )
            return

        print(f"Loaded {len(gdf)} cells. Generating map...")

        fig, ax = plt.subplots(figsize=(12, 10))

        gdf.plot(
            column="baseline_vulnerability",
            cmap="YlOrRd",
            legend=True,
            legend_kwds={"label": "Vulnerability Score (0-1)"},
            ax=ax,
            edgecolor="black",
            linewidth=0.1,
            alpha=0.8,
        )

        ax.set_title(
            "PJ Baseline Vulnerability - Imputation Model Sanity Check", fontsize=14
        )
        ax.set_axis_off()

        output_path = ARTIFACTS_DIR / "vulnerability_choropleth.png"
        plt.savefig(output_path, dpi=300, bbox_inches="tight")
        print(f"SUCCESS: Choropleth saved to {output_path}")

    except Exception as e:
        print(f"Error during visualization: {e}")


if __name__ == "__main__":
    visualize()
