import geopandas as gpd
import os

input_shp = "../../pj_mvp_data/pj_roads.shp"
output_geojson = "../../apps/frontend/public/data/pj_routes.geojson"

print("Converting shapefile to GeoJSON...")

# Ensure output directory exists
os.makedirs("../../apps/frontend/public/data", exist_ok=True)

gdf = gpd.read_file(input_shp)

# IMPORTANT: Reproject to WGS84 (MapLibre requirement)
gdf = gdf.to_crs(epsg=4326)

gdf.to_file(output_geojson, driver="GeoJSON")

print("Route GeoJSON exported successfully.")