"""Validate SQL routing integration against a live Postgres database."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

ROOT_DIR = Path(__file__).resolve().parents[1]
API_SRC = ROOT_DIR / "apps" / "api" / "src"
for path in (str(ROOT_DIR), str(API_SRC)):
    if path not in sys.path:
        sys.path.insert(0, path)

from fastapi.testclient import TestClient  # noqa: E402

from app.core.config import get_settings  # noqa: E402
from app.main import create_app  # noqa: E402


def _default_database_url() -> str:
    """Resolve DATABASE_URL from env first, then .env-backed app settings."""
    database_url = os.getenv("DATABASE_URL", "").strip()
    if database_url:
        return database_url
    try:
        return get_settings().database_url
    except Exception:  # noqa: BLE001
        return ""


def parse_args() -> argparse.Namespace:
    """Parse script arguments."""
    default_db_url = _default_database_url()
    parser = argparse.ArgumentParser(
        description="Validate routing SQL compatibility objects and route endpoint."
    )
    parser.add_argument(
        "--database-url",
        default=default_db_url,
        help="Postgres URL used by routing SQL backend.",
    )
    parser.add_argument(
        "--max-attempts",
        type=int,
        default=12,
        help="Max attempts to find a routable start/end pair.",
    )
    return parser.parse_args()


def assert_compatibility_objects(engine: Engine) -> None:
    """Verify compatibility schema objects and required columns exist."""
    with engine.connect() as conn:
        column_count = conn.execute(
            text(
                """
                SELECT COUNT(*)::integer
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'roads_edges'
                  AND column_name IN (
                    'base_cost', 'risk_penalty', 'agg_cost', 'agg_reverse_cost', 'length'
                  );
                """
            )
        ).scalar_one()
        if int(column_count) != 5:
            raise RuntimeError(
                "roads_edges is missing one or more compatibility columns"
            )

        view_exists = conn.execute(
            text("SELECT to_regclass('public.pj_roads') IS NOT NULL;")
        ).scalar_one()
        if not bool(view_exists):
            raise RuntimeError("public.pj_roads view is missing")

        mv_exists = conn.execute(
            text("SELECT to_regclass('public.pj_roads_vertices_pgr') IS NOT NULL;")
        ).scalar_one()
        if not bool(mv_exists):
            raise RuntimeError("public.pj_roads_vertices_pgr materialized view is missing")

        refresh_fn_exists = conn.execute(
            text(
                "SELECT to_regprocedure('public.refresh_pj_roads_vertices_pgr()') IS NOT NULL;"
            )
        ).scalar_one()
        if not bool(refresh_fn_exists):
            raise RuntimeError("public.refresh_pj_roads_vertices_pgr() is missing")


def _sample_start_nodes(engine: Engine, limit: int) -> list[int]:
    """Return random source-node IDs as route start candidates."""
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT id
                FROM (
                    SELECT DISTINCT source AS id
                    FROM public.pj_roads
                    WHERE source IS NOT NULL
                ) AS sources
                ORDER BY RANDOM()
                LIMIT :limit;
                """
            ),
            {"limit": limit},
        ).mappings().all()
    return [int(row["id"]) for row in rows]


def _sample_edge_pairs(engine: Engine, limit: int) -> list[tuple[int, int]]:
    """Return random directed edge node pairs from pj_roads."""
    with engine.connect() as conn:
        rows = conn.execute(
            text(
                """
                SELECT source, target
                FROM public.pj_roads
                WHERE source IS NOT NULL
                  AND target IS NOT NULL
                  AND agg_cost IS NOT NULL
                  AND agg_cost > 0
                ORDER BY RANDOM()
                LIMIT :limit;
                """
            ),
            {"limit": limit},
        ).mappings().all()
    return [(int(row["source"]), int(row["target"])) for row in rows]


def _get_node(engine: Engine, node_id: int) -> dict[str, Any]:
    """Return node coordinates for a vertex ID."""
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT
                    id,
                    extensions.ST_Y(the_geom) AS lat,
                    extensions.ST_X(the_geom) AS lon
                FROM public.pj_roads_vertices_pgr
                WHERE id = :node_id;
                """
            ),
            {"node_id": node_id},
        ).mappings().first()
    if row is None:
        raise RuntimeError(f"node not found in pj_roads_vertices_pgr: {node_id}")
    return dict(row)


def _has_path(engine: Engine, start_node: int, end_node: int) -> bool:
    """Check if pgr_dijkstra can find a path between two nodes."""
    if start_node == end_node:
        return False
    with engine.connect() as conn:
        row_count = conn.execute(
            text(
                """
                SELECT COUNT(*)::integer
                FROM pgr_dijkstra(
                    'SELECT id, source, target, agg_cost AS cost, agg_reverse_cost AS reverse_cost FROM public.pj_roads',
                    :start_node,
                    :end_node,
                    directed := true
                )
                WHERE edge <> -1;
                """
            ),
            {"start_node": start_node, "end_node": end_node},
        ).scalar_one()
    return int(row_count) > 0


def _find_reachable_end_node(engine: Engine, start_node: int) -> int | None:
    """Find one node reachable from start_node using directed routing costs."""
    with engine.connect() as conn:
        row = conn.execute(
            text(
                """
                SELECT dd.node::bigint AS node
                FROM pgr_drivingDistance(
                    'SELECT id, source, target, agg_cost AS cost, agg_reverse_cost AS reverse_cost FROM public.pj_roads',
                    :start_node,
                    1000000000,
                    directed := true
                ) AS dd
                WHERE dd.node <> :start_node
                ORDER BY random()
                LIMIT 1;
                """
            ),
            {"start_node": start_node},
        ).mappings().first()
    if row is None:
        return None
    return int(row["node"])


def find_routable_pair(engine: Engine, max_attempts: int) -> tuple[dict[str, Any], dict[str, Any]]:
    """Find a directed-routable start/end node pair for endpoint verification."""
    # First pass: try pairs from existing directed edges in pj_roads.
    for start_node_id, end_node_id in _sample_edge_pairs(engine, limit=max_attempts):
        if not _has_path(engine, start_node_id, end_node_id):
            continue
        try:
            start_node = _get_node(engine, start_node_id)
            end_node = _get_node(engine, end_node_id)
        except RuntimeError:
            continue
        return start_node, end_node

    # Fallback: expand from random starts to any reachable directed node.
    candidate_starts = _sample_start_nodes(engine, limit=max_attempts)
    for start_node_id in candidate_starts:
        end_node_id = _find_reachable_end_node(engine, start_node_id)
        if end_node_id is None:
            continue
        if _has_path(engine, start_node_id, end_node_id):
            start_node = _get_node(engine, start_node_id)
            end_node = _get_node(engine, end_node_id)
            return start_node, end_node
    raise RuntimeError(
        "failed to find a directed-routable node pair from pj_roads_vertices_pgr; "
        "check that public.pj_roads has valid source/target/cost fields and that "
        "graph topology is populated"
    )


def validate_route_endpoint(database_url: str, start: dict[str, Any], end: dict[str, Any]) -> None:
    """Call /api/v1/route with SQL backend and assert a valid response."""
    os.environ["ROUTING_BACKEND"] = "sql"
    os.environ["DATABASE_URL"] = database_url
    os.environ["ROUTING_ALGORITHM"] = "dijkstra"

    get_settings.cache_clear()

    app = create_app()
    with TestClient(app) as client:
        response = client.get(
            "/api/v1/route",
            params={
                "origin_lat": start["lat"],
                "origin_lng": start["lon"],
                "destination_lat": end["lat"],
                "destination_lng": end["lon"],
            },
        )
    if response.status_code != 200:
        raise RuntimeError(
            f"/api/v1/route returned {response.status_code}: {response.text}"
        )
    payload = response.json()
    if payload.get("route_geojson", {}).get("type") != "FeatureCollection":
        raise RuntimeError("route_geojson is not a FeatureCollection")
    if payload.get("distance_meters", 0) <= 0:
        raise RuntimeError("distance_meters must be positive")
    if payload.get("eta_minutes", 0) <= 0:
        raise RuntimeError("eta_minutes must be positive")


def main() -> None:
    """Run schema and endpoint verification for SQL routing backend."""
    args = parse_args()
    if not args.database_url:
        raise RuntimeError(
            "missing database URL; set --database-url or DATABASE_URL"
        )

    engine = create_engine(args.database_url, pool_pre_ping=True)
    assert_compatibility_objects(engine)
    start_node, end_node = find_routable_pair(engine, args.max_attempts)
    validate_route_endpoint(args.database_url, start_node, end_node)
    print("Routing SQL integration validation passed.")
    print(
        f"Verified route from node {start_node['id']} to {end_node['id']} "
        f"({start_node['lat']}, {start_node['lon']}) -> ({end_node['lat']}, {end_node['lon']})."
    )


if __name__ == "__main__":
    main()
