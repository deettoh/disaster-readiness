"""Provides a standardized query contract that returns distance, ETA, and GeoJSON geometries for any PJ coordinate pair."""

import json

from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql://postgres:root@localhost:5432/routing_db"


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
        }
    """
    engine = create_engine(DATABASE_URL)

    with engine.connect() as conn:
        # Snap Start Node
        snap_sql = """
            SELECT id FROM pj_roads_vertices_pgr
            ORDER BY the_geom <-> ST_SetSRID(ST_Point(:lon, :lat), 4326)
            LIMIT 1;
        """

        start_node = conn.execute(
            text(snap_sql), {"lon": start_lon, "lat": start_lat}
        ).fetchone()

        end_node = conn.execute(
            text(snap_sql), {"lon": end_lon, "lat": end_lat}
        ).fetchone()

        if not start_node or not end_node:
            return {"status": "error", "message": "Could not snap coordinates."}

        start_node = start_node[0]
        end_node = end_node[0]

        if start_node == end_node:
            return {
                "status": "success",
                "distance_km": 0,
                "eta_minutes": 0,
                "geojson": None,
            }

        # Routing Query
        routing_sql = f"""
            WITH path AS (
                SELECT * FROM pgr_{algorithm}(
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

        result = conn.execute(
            text(routing_sql), {"start": start_node, "end": end_node}
        ).fetchone()

        if not result or result[2] is None:
            return {"status": "error", "message": "No route found."}

        total_dist_m = result[0]
        total_time_s = result[1]
        geojson_geom = json.loads(result[2])

        return {
            "status": "success",
            "distance_km": round(total_dist_m / 1000, 2),
            "eta_minutes": round(total_time_s / 60, 2),
            "geojson": {
                "type": "Feature",
                "geometry": geojson_geom,
                "properties": {"source": start_node, "target": end_node},
            },
        }
