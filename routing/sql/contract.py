"""Provides standardized routing contract helpers for backend integration."""

from __future__ import annotations

import json
from typing import Any

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError


def _normalize_algorithm(algorithm: str) -> str:
    """Validate and normalize algorithm name for pgRouting selection."""
    normalized = algorithm.lower()
    if normalized not in {"dijkstra", "astar"}:
        raise ValueError("algorithm must be one of: dijkstra, astar")
    return normalized


def get_route(
    start_lat: float,
    start_lon: float,
    end_lat: float,
    end_lon: float,
    *,
    algorithm: str = "dijkstra",
    engine: Engine,
) -> dict[str, Any]:
    """Compute route and return the standardized routing contract payload."""
    normalized_algorithm = _normalize_algorithm(algorithm)

    snap_sql = text(
        """
        SELECT id FROM pj_roads_vertices_pgr
        ORDER BY the_geom <-> ST_SetSRID(ST_Point(:lon, :lat), 4326)
        LIMIT 1;
        """
    )
    route_sql = text(
        f"""
        WITH path AS (
            SELECT * FROM pgr_{normalized_algorithm}(
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
            SUM(length) as total_dist_m,
            SUM(agg_cost) as total_time_s,
            ST_AsGeoJSON(ST_LineMerge(ST_Collect(geometry))) as geojson_geom
        FROM route_segments;
        """
    )

    try:
        with engine.connect() as conn:
            start_node_row = conn.execute(
                snap_sql, {"lon": start_lon, "lat": start_lat}
            ).fetchone()
            end_node_row = conn.execute(
                snap_sql, {"lon": end_lon, "lat": end_lat}
            ).fetchone()

            if not start_node_row or not end_node_row:
                return {"status": "error", "message": "Could not snap coordinates."}

            start_node = start_node_row[0]
            end_node = end_node_row[0]

            if start_node == end_node:
                return {
                    "status": "success",
                    "distance_km": 0.0,
                    "eta_minutes": 0.0,
                    "geojson": None,
                }

            result = conn.execute(
                route_sql, {"start": start_node, "end": end_node}
            ).fetchone()
    except SQLAlchemyError as exc:
        raise RuntimeError("failed to execute routing contract SQL") from exc

    if not result or result[2] is None:
        return {"status": "error", "message": "No route found."}

    geojson_geom = json.loads(str(result[2]))
    return {
        "status": "success",
        "distance_km": round(float(result[0]) / 1000, 2),
        "eta_minutes": round(float(result[1]) / 60, 2),
        "geojson": {
            "type": "Feature",
            "geometry": geojson_geom,
            "properties": {"source": start_node, "target": end_node},
        },
    }
