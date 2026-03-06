"""Provides standardized routing contract helpers for backend integration."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

from apps.api.src.app.core.config import get_settings
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

# 1. Load Settings from Centralized Configuration
settings = get_settings()

# Database Setup (Internal default engine)
# Using centralized settings for the URL
DATABASE_URL = settings.database_url
default_engine = create_engine(DATABASE_URL)

# Bounding Box (Defaults to Petaling Jaya area)
# Using os.getenv as a fallback since these are not yet in the Settings class
PJ_BOUNDS = {
    "min_lat": float(os.getenv("PJ_MIN_LAT", 3.03)),
    "max_lat": float(os.getenv("PJ_MAX_LAT", 3.17)),
    "min_lon": float(os.getenv("PJ_MIN_LON", 101.55)),
    "max_lon": float(os.getenv("PJ_MAX_LON", 101.66))
}

def validate_coordinates(lat: float, lon: float) -> tuple[bool, str]:
    """Checks if coordinates are within the PJ service area."""
    if lat is None or lon is None:
        return False, "Coordinates cannot be null."

    in_bounds = (PJ_BOUNDS["min_lat"] <= lat <= PJ_BOUNDS["max_lat"] and
                 PJ_BOUNDS["min_lon"] <= lon <= PJ_BOUNDS["max_lon"])

    if not in_bounds:
        return False, f"Coordinates ({lat}, {lon}) are outside the PJ service area."

    return True, "Valid"

def _normalize_algorithm(algorithm: str) -> str:
    """Validate and normalize algorithm name."""
    normalized = algorithm.lower()
    if normalized not in {"dijkstra", "astar"}:
        raise ValueError("algorithm must be one of: dijkstra, astar")
    return normalized

def get_route(  # noqa: D417
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    algorithm: str = "dijkstra",
    engine: Engine | None = None
) -> dict[str, Any]:
    """Standardized Routing Contract.

    Args:
        start_lat, start_lon: Start coordinates.
        end_lat, end_lon: End coordinates.
        algorithm: "dijkstra" or "astar".
        engine: Optional SQLAlchemy engine. Uses default if None.
    """
    # 1. Coordinate Validation
    for label, lat, lon in [("Start", start_lat, start_lon), ("End", end_lat, end_lon)]:
        is_valid, msg = validate_coordinates(lat, lon)
        if not is_valid:
            return {"status": "error", "error_type": "VALIDATION_ERROR", "message": f"{label}: {msg}"}

    # Use provided engine or fall back to default
    routing_engine = engine or default_engine
    normalized_alg = _normalize_algorithm(algorithm)

    try:
        with routing_engine.connect() as conn:
            # Snap Coordinates
            snap_sql = text("""
                SELECT id FROM pj_roads_vertices_pgr
                ORDER BY the_geom <-> ST_SetSRID(ST_Point(:lon, :lat), 4326)
                LIMIT 1;
            """)

            start_node_row = conn.execute(snap_sql, {"lon": start_lon, "lat": start_lat}).fetchone()
            end_node_row = conn.execute(snap_sql, {"lon": end_lon, "lat": end_lat}).fetchone()

            if not start_node_row or not end_node_row:
                return {"status": "error", "message": "Could not snap coordinates to road network."}

            u, v = start_node_row[0], end_node_row[0]

            if u == v:
                return {"status": "success", "distance_km": 0.0, "eta_minutes": 0.0, "geojson": None}

            # Execute pgRouting
            route_sql = text(f"""
                WITH path AS (
                    SELECT * FROM pgr_{normalized_alg}(
                        'SELECT id, source, target, agg_cost AS cost, agg_reverse_cost AS reverse_cost FROM pj_roads',
                        :start, :end, directed := true
                    )
                ),
                route_segments AS (
                    SELECT p.seq, r.length, r.agg_cost, r.geometry
                    FROM path p
                    JOIN pj_roads r ON p.edge = r.id
                    ORDER BY p.seq
                )
                SELECT
                    COALESCE(SUM(length), 0) as total_dist_m,
                    COALESCE(SUM(agg_cost), 0) as total_time_s,
                    ST_AsGeoJSON(ST_LineMerge(ST_Collect(geometry))) as geojson_geom
                FROM route_segments;
            """)

            result = conn.execute(route_sql, {"start": u, "end": v}).fetchone()

            if not result or result[2] is None:
                return {"status": "error", "message": "No route found between selected points."}

            # Build Response
            return {
                "status": "success",
                "distance_km": round(float(result[0]) / 1000, 2),
                "eta_minutes": round(float(result[1]) / 60, 2),
                "geojson": {
                    "type": "Feature",
                    "geometry": json.loads(result[2]),
                    "properties": {
                        "source_node": u,
                        "target_node": v,
                        "algorithm": normalized_alg
                    }
                }
            }

    except SQLAlchemyError as e:
        logging.error(f"Database error in get_route: {e}")
        return {"status": "error", "message": "Routing engine database error."}
    except Exception as e:
        logging.error(f"Unexpected error in get_route: {e}")
        return {"status": "error", "message": str(e)}
