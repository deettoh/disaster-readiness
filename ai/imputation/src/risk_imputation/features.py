"""Feature extraction module for the risk imputation model.

Extracts per-grid-cell features from geospatial data sources for training
and inference. This module provides the same feature extraction logic used
in the Jupyter notebook, packaged as reusable functions.

Data sources:
    - SRTM 30m elevation raster (tifffile)
    - OSM waterway lines (geopandas)
    - JPS flood hotspot points (pandas CSV)
    - Cell accessibility handoff (pandas CSV)
"""

from __future__ import annotations

import logging
import re
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point
from shapely.ops import unary_union

logger = logging.getLogger(__name__)

# PJ bounding box (EPSG:4326)
PJ_BBOX = (101.58, 3.08, 101.70, 3.17)


class ElevationSampler:
    """Samples elevation and slope values from a GeoTIFF or .hgt raster."""

    def __init__(self, srtm_path: Path) -> None:
        """Initialize sampler from either a GeoTIFF or an .hgt elevation raster."""
        # Raw SRTM .hgt format: Big-endian 16-bit signed integers
        size = srtm_path.stat().st_size
        dim = int(np.sqrt(size / 2))
        self.data = np.fromfile(srtm_path, dtype=">i2").reshape((dim, dim))

        # Parsing NXXEXXX filename for origin
        match = re.search(r"([NS])(\d+)([EW])(\d+)", srtm_path.name)
        if match:
            ns, lat_deg, ew, lon_deg = match.groups()
            # N03 means south edge is 3, top edge is 4. Data is top-down.
            self.y_origin = float(lat_deg) + 1.0 if ns == "N" else -float(lat_deg)
            self.x_origin = float(lon_deg) if ew == "E" else -float(lon_deg)
        else:
            self.y_origin = 4.0
            self.x_origin = 101.0

        self.dx = 1.0 / (dim - 1)
        self.dy = 1.0 / (dim - 1)
        self.rows, self.cols = dim, dim

        logger.info(
            "Loaded elevation raster %s (%dx%d), range [%d, %d]m",
            srtm_path.name,
            self.cols,
            self.rows,
            self.data.min(),
            self.data.max(),
        )

    def elevation_at(self, lon: float, lat: float) -> float:
        """Sample elevation (meters) at a lon/lat coordinate."""
        col = int((lon - self.x_origin) / self.dx)
        row = int((self.y_origin - lat) / self.dy)
        if 0 <= row < self.rows and 0 <= col < self.cols:
            return float(self.data[row, col])
        return np.nan

    def slope_at(self, lon: float, lat: float) -> float:
        """Compute slope (degrees) at a point using 3x3 Sobel gradient."""
        col = int((lon - self.x_origin) / self.dx)
        row = int((self.y_origin - lat) / self.dy)
        if not (1 <= row < self.rows - 1 and 1 <= col < self.cols - 1):
            return np.nan
        cell_size_m = self.dx * 111320 * np.cos(np.radians(lat))
        dz_dx = (
            float(self.data[row - 1, col + 1])
            + 2 * float(self.data[row, col + 1])
            + float(self.data[row + 1, col + 1])
            - float(self.data[row - 1, col - 1])
            - 2 * float(self.data[row, col - 1])
            - float(self.data[row + 1, col - 1])
        ) / (8 * cell_size_m)
        dz_dy = (
            float(self.data[row + 1, col - 1])
            + 2 * float(self.data[row + 1, col])
            + float(self.data[row + 1, col + 1])
            - float(self.data[row - 1, col - 1])
            - 2 * float(self.data[row - 1, col])
            - float(self.data[row - 1, col + 1])
        ) / (8 * cell_size_m)
        return float(np.degrees(np.arctan(np.sqrt(dz_dx**2 + dz_dy**2))))


def load_waterways(geojson_path: Path) -> gpd.GeoDataFrame:
    """Load and clip waterways to PJ bounding box."""
    logger.info("Loading waterways from %s ...", geojson_path)
    gdf = gpd.read_file(str(geojson_path), bbox=PJ_BBOX)
    logger.info("Loaded %d waterway features within PJ bbox", len(gdf))
    return gdf


def load_hotspots(csv_path: Path) -> gpd.GeoDataFrame:
    """Load flood hotspot points from CSV."""
    df = pd.read_csv(csv_path)
    gdf = gpd.GeoDataFrame(
        df,
        geometry=gpd.points_from_xy(df["lng"], df["lat"]),
        crs="EPSG:4326",
    )
    logger.info("Loaded %d flood hotspot points", len(gdf))
    return gdf


def extract_features(
    cell_centroids: dict[int, tuple[float, float]],
    elevation_sampler: ElevationSampler,
    waterways_gdf: gpd.GeoDataFrame,
    hotspots_gdf: gpd.GeoDataFrame,
    accessibility_df: pd.DataFrame,
) -> pd.DataFrame:
    """Extract all features for each grid cell.

    Args:
        cell_centroids: Mapping of cell_id -> (lon, lat).
        elevation_sampler: ElevationSampler instance.
        waterways_gdf: Waterway lines GeoDataFrame (EPSG:4326).
        hotspots_gdf: Hotspot points GeoDataFrame (EPSG:4326).
        accessibility_df: DataFrame with cell_id, avg_road_density, avg_travel_time_to_shelter_seconds.

    Returns:
        DataFrame with one row per cell and all feature columns.
    """
    # Preproject for distance calculations
    waterways_utm = waterways_gdf.to_crs("EPSG:32647")
    waterways_union = unary_union(waterways_utm.geometry)
    hotspots_utm = hotspots_gdf.to_crs("EPSG:32647")
    hotspots_union = unary_union(hotspots_utm.geometry)

    acc_lookup = accessibility_df.set_index("cell_id")
    records = []

    for i, (cid, (lon, lat)) in enumerate(cell_centroids.items()):
        if (i + 1) % 50 == 0:
            logger.info("Processing cell %d/%d...", i + 1, len(cell_centroids))

        pt_utm = (
            gpd.GeoDataFrame(geometry=[Point(lon, lat)], crs="EPSG:4326")
            .to_crs("EPSG:32647")
            .geometry.iloc[0]
        )

        records.append(
            {
                "cell_id": cid,
                "centroid_lon": lon,
                "centroid_lat": lat,
                "mean_elevation": elevation_sampler.elevation_at(lon, lat),
                "mean_slope": elevation_sampler.slope_at(lon, lat),
                "dist_to_river_m": pt_utm.distance(waterways_union),
                "dist_to_hotspot_m": pt_utm.distance(hotspots_union),
                "road_density": acc_lookup.loc[cid, "avg_road_density"]
                if cid in acc_lookup.index
                else 0.0,
                "travel_time_to_shelter_s": acc_lookup.loc[
                    cid, "avg_travel_time_to_shelter_seconds"
                ]
                if cid in acc_lookup.index
                else np.nan,
            }
        )

    df = pd.DataFrame(records)
    logger.info(
        "Feature extraction complete: %d cells, %d columns", len(df), len(df.columns)
    )
    return df


def build_proxy_label(
    df: pd.DataFrame,
    *,
    w_hotspot: float = 0.50,
    w_elevation: float = 0.25,
    w_river: float = 0.25,
    hotspot_buffer_m: float = 500,
    hotspot_max_dist_m: float = 2000,
    river_max_dist_m: float = 1000,
) -> pd.DataFrame:
    """Construct proxy vulnerability label from features.

    Args:
        df: Feature DataFrame (must have dist_to_hotspot_m, mean_elevation, dist_to_river_m).
        w_hotspot: Weight for hotspot proximity component.
        w_elevation: Weight for low elevation component.
        w_river: Weight for river proximity component.
        hotspot_buffer_m: Distance within which hotspot score is 1.0.
        hotspot_max_dist_m: Distance at which hotspot score decays to 0.
        river_max_dist_m: Distance at which river score decays to 0.

    Returns:
        DataFrame with added vulnerability_label column.
    """
    result = df.copy()

    # Hotspot proximity
    result["hotspot_proximity"] = np.clip(
        1.0
        - (result["dist_to_hotspot_m"] - hotspot_buffer_m)
        / (hotspot_max_dist_m - hotspot_buffer_m),
        0,
        1,
    )
    result.loc[result["dist_to_hotspot_m"] <= hotspot_buffer_m, "hotspot_proximity"] = (
        1.0
    )

    # Low elevation (inverted)
    elev_min, elev_max = result["mean_elevation"].min(), result["mean_elevation"].max()
    result["low_elevation"] = 1.0 - (result["mean_elevation"] - elev_min) / (
        elev_max - elev_min + 1e-8
    )

    # River proximity
    result["river_proximity"] = np.clip(
        1.0 - result["dist_to_river_m"] / river_max_dist_m, 0, 1
    )

    # Weighted label
    result["vulnerability_label"] = (
        w_hotspot * result["hotspot_proximity"]
        + w_elevation * result["low_elevation"]
        + w_river * result["river_proximity"]
    ).clip(0, 1)

    logger.info(
        "Proxy label stats: min=%.3f, max=%.3f, mean=%.3f",
        result["vulnerability_label"].min(),
        result["vulnerability_label"].max(),
        result["vulnerability_label"].mean(),
    )
    return result
