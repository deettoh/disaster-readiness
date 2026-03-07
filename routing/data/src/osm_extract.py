"""Downloads and exports road network data for Petaling Jaya, Malaysia, using OSMnx."""

import os
from typing import cast

import geopandas as gpd
import osmnx as ox
from apps.api.src.app.core.config import get_settings

settings = get_settings()

def download_pj_road_graph():
    """Extracts PJ road data, saves it as a Shapefile, and plots the graph."""
    print(f"--- {settings.app_name}: Data Extraction ---")
    print(f"Target Environment: {settings.app_env.upper()}")

    place_name = "Petaling Jaya, Selangor, Malaysia"
    print(f"Starting extraction for: {place_name}...")

    # Download the 'drive' network
    graph = ox.graph_from_place(place_name, network_type="drive")

    # Project the graph to a local CRS (UTM)
    graph_projected = ox.project_graph(graph)

    # FIX: Explicitly cast to GeoDataFrame to satisfy Pylance/Type Checkers
    nodes_raw, edges_raw = ox.graph_to_gdfs(graph_projected)
    nodes = cast(gpd.GeoDataFrame, nodes_raw)
    edges = cast(gpd.GeoDataFrame, edges_raw)

    # Output configuration relative to project root
    output_folder = "routing/data/pj_mvp_data"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # Save the data (Shapefile expects a directory or .shp file)
    output_path = os.path.join(output_folder, "pj_roads.shp")

    # .to_file will now be recognized by Pylance
    edges.to_file(output_path)

    print(f"SUCCESS: Road graph saved to {output_path}")
    print(f"Stats: {len(nodes)} nodes and {len(edges)} road segments extracted.")

    # Integration Check: Safety log to show where we're pointing
    db_host = settings.database_url.split('@')[-1]
    print(f"Configured for Database: {db_host}")

    # Optional: Plot for visual verification
    # ox.plot_graph(graph)

if __name__ == "__main__":
    try:
        download_pj_road_graph()
    except Exception as e:
        print(f"CRITICAL ERROR during OSM extraction: {e}")

