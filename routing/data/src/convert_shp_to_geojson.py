"""Convert PJ roads shapefile to GeoJSON."""

import os
from pathlib import Path

import geopandas as gpd

BASE_DIR = Path(__file__).parent.resolve()

input_shp = BASE_DIR.parent / "pj_mvp_data" / "pj_roads.shp"

output_geojson = (
    BASE_DIR.parents[2] / "apps" / "frontend" / "public" / "pj_routes.geojson"
)

print(f"Converting shapefile to GeoJSON: {input_shp}")

os.makedirs(output_geojson.parent, exist_ok=True)

gdf = gpd.read_file(str(input_shp))

# IMPORTANT: Reproject to WGS84 (MapLibre requirement)
gdf = gdf.to_crs(epsg=4326)

gdf.to_file(str(output_geojson), driver="GeoJSON")

print(f"Route GeoJSON exported successfully to: {output_geojson}")
