"""Provides a standardized query contract that returns distance, ETA, and GeoJSON geometries for any PJ coordinate pair."""

import json
import logging
import os

from dotenv import load_dotenv
from sqlalchemy import create_engine, text

# 1. Load Environment Variables
load_dotenv()

# Database Setup
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "root")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "routing_db")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

# Bounding Box (Defaults to Petaling Jaya area)
PJ_BOUNDS = {
    "min_lat": float(os.getenv("PJ_MIN_LAT", 3.03)),
    "max_lat": float(os.getenv("PJ_MAX_LAT", 3.17)),
    "min_lon": float(os.getenv("PJ_MIN_LON", 101.55)),
    "max_lon": float(os.getenv("PJ_MAX_LON", 101.66))
}

def validate_coordinates(lat, lon):
    """Checks if coordinates are within the PJ service area defined in .env."""
    if lat is None or lon is None:
        return False, "Coordinates cannot be null."

    in_bounds = (PJ_BOUNDS["min_lat"] <= lat <= PJ_BOUNDS["max_lat"] and
                 PJ_BOUNDS["min_lon"] <= lon <= PJ_BOUNDS["max_lon"])

    if not in_bounds:
        return False, f"Coordinates ({lat}, {lon}) are outside the PJ service area."

    return True, "Valid"

def get_route(start_lat, start_lon, end_lat, end_lon, algorithm="dijkstra"):
    """Official Routing Query Contract (For Member A).
    Input:
        start_lat, start_lon
        end_lat, end_lon
        algorithm: "dijkstra" or "astar"
    Returns:
        {
            "status": "success" | "error",
            "distance_km": float,
            "eta_minutes": float,
            "geojson": {...}
        }.
    """  # noqa: D205
    # 1. Validation
    for label, lat, lon in [("Start", start_lat, start_lon), ("End", end_lat, end_lon)]:
        is_valid, msg = validate_coordinates(lat, lon)
        if not is_valid:
            return {"status": "error", "error_type": "VALIDATION_ERROR", "message": f"{label}: {msg}"}

    try:
        with engine.connect() as conn:
            # 2. Snap Coordinates to Nearest Road Nodes
            snap_sql = """
                SELECT id FROM pj_roads_vertices_pgr
                ORDER BY the_geom <-> ST_SetSRID(ST_Point(:lon, :lat), 4326)
                LIMIT 1;
            """

            start_node = conn.execute(text(snap_sql), {"lon": start_lon, "lat": start_lat}).fetchone()
            end_node = conn.execute(text(snap_sql), {"lon": end_lon, "lat": end_lat}).fetchone()

            if not start_node or not end_node:
                return {"status": "error", "message": "Could not locate nearest road nodes."}

            u, v = start_node[0], end_node[0]

            if u == v:
                return {"status": "success", "distance_km": 0.0, "eta_minutes": 0.0, "geojson": None}

            # 3. Dynamic Algorithm Configuration
            if algorithm.lower() == "astar":
                pgr_func = "pgr_astar"
                inner_query = """
                    SELECT id, source, target, agg_cost AS cost, agg_reverse_cost AS reverse_cost,
                    ST_X(ST_StartPoint(geometry)) AS x1, ST_Y(ST_StartPoint(geometry)) AS y1,
                    ST_X(ST_EndPoint(geometry)) AS x2, ST_Y(ST_EndPoint(geometry)) AS y2
                    FROM pj_roads
                """
                params = {"start": u, "end": v, "heuristic": 5}
                extra_args = ", heuristic := :heuristic"
            else:
                pgr_func = "pgr_dijkstra"
                inner_query = "SELECT id, source, target, agg_cost AS cost, agg_reverse_cost AS reverse_cost FROM pj_roads"
                params = {"start": u, "end": v}
                extra_args = ""

            # 4. Execute Pathfinding and Geometry Aggregation
            routing_sql = f"""
                WITH path AS (
                    SELECT * FROM {pgr_func}(
                        '{inner_query}',
                        :start, :end, directed := true {extra_args}
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
            """

            result = conn.execute(text(routing_sql), params).fetchone()

            if not result or result[2] is None:
                return {"status": "error", "message": "No route found between selected points."}

            # 5. Success Response
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
                        "algorithm": algorithm
                    }
                }
            }

    except Exception as e:
        logging.error(f"Critical error in get_route: {e}")
        return {"status": "error", "message": "The routing engine encountered an internal database error."}
