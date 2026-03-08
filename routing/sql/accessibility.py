"""Compute and validate per-cell accessibility for readiness scoring."""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from apps.api.src.app.core.config import get_settings
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

settings = get_settings()

DEFAULT_HANDOFF_PATH = Path("routing/artifacts/cell_accessibility_handoff.csv")


@dataclass
class AccessibilitySummary:
    """Summary metrics for accessibility computation validation."""

    total_cells: int
    with_travel_time: int
    with_density: int
    min_seconds: int | None
    max_seconds: int | None


class AccessibilityManager:
    """Compute and persist canonical public.cell_accessibility metrics."""

    def __init__(
        self,
        *,
        database_url: str | None = None,
        engine: Engine | None = None,
    ) -> None:
        """Initialize the DB engine for accessibility processing."""
        self._database_url = database_url or settings.database_url
        self.engine = engine or create_engine(self._database_url, pool_pre_ping=True)

    def compute_accessibility(self) -> int:
        """Populate public.cell_accessibility from grid, shelter, and route graph data."""
        self._ensure_prerequisites()
        compute_sql = text(
            """
            WITH shelter_nodes AS (
                SELECT ARRAY_AGG(DISTINCT v.id)::bigint[] AS ids
                FROM public.shelters AS s
                JOIN LATERAL (
                    SELECT pvv.id
                    FROM public.pj_roads_vertices_pgr AS pvv
                    ORDER BY pvv.the_geom <-> s.geom
                    LIMIT 1
                ) AS v ON TRUE
            ),
            cell_nodes AS (
                SELECT
                    gc.id AS cell_id,
                    v.id AS start_node
                FROM public.grid_cells AS gc
                JOIN LATERAL (
                    SELECT pvv.id
                    FROM public.pj_roads_vertices_pgr AS pvv
                    ORDER BY pvv.the_geom <-> extensions.ST_Centroid(gc.geom)
                    LIMIT 1
                ) AS v ON TRUE
            ),
            route_costs AS (
                SELECT
                    rc.start_vid,
                    AVG(rc.agg_cost) AS avg_cost_sec
                FROM pgr_dijkstraCost(
                    'SELECT id, source, target, agg_cost AS cost, agg_reverse_cost AS reverse_cost FROM public.pj_roads',
                    (SELECT ARRAY_AGG(DISTINCT cn.start_node)::bigint[] FROM cell_nodes AS cn),
                    (SELECT ids FROM shelter_nodes),
                    directed := TRUE
                ) AS rc
                GROUP BY rc.start_vid
            ),
            route_by_cell AS (
                SELECT
                    cn.cell_id,
                    ROUND(rc.avg_cost_sec)::integer AS avg_travel_time_to_shelter_seconds
                FROM cell_nodes AS cn
                LEFT JOIN route_costs AS rc ON rc.start_vid = cn.start_node
            ),
            density_by_cell AS (
                SELECT
                    gc.id AS cell_id,
                    ROUND(
                        COALESCE(
                            (
                                SUM(
                                    extensions.ST_Length(
                                        extensions.ST_Intersection(pr.geometry, gc.geom)::extensions.geography
                                    )
                                ) / 1000.0
                            ) / NULLIF(
                                extensions.ST_Area(gc.geom::extensions.geography) / 1000000.0,
                                0
                            ),
                            0
                        )::numeric,
                        3
                    ) AS avg_road_density
                FROM public.grid_cells AS gc
                LEFT JOIN public.pj_roads AS pr
                    ON extensions.ST_Intersects(pr.geometry, gc.geom)
                GROUP BY gc.id, gc.geom
            )
            INSERT INTO public.cell_accessibility (
                cell_id,
                avg_travel_time_to_shelter_seconds,
                avg_road_density,
                updated_at
            )
            SELECT
                gc.id AS cell_id,
                rb.avg_travel_time_to_shelter_seconds,
                db.avg_road_density,
                NOW() AS updated_at
            FROM public.grid_cells AS gc
            LEFT JOIN route_by_cell AS rb ON rb.cell_id = gc.id
            LEFT JOIN density_by_cell AS db ON db.cell_id = gc.id
            ON CONFLICT (cell_id) DO UPDATE
            SET
                avg_travel_time_to_shelter_seconds = EXCLUDED.avg_travel_time_to_shelter_seconds,
                avg_road_density = EXCLUDED.avg_road_density,
                updated_at = EXCLUDED.updated_at;
            """
        )
        with self.engine.connect() as conn:
            conn.execute(compute_sql)
            conn.commit()
            count = conn.execute(
                text("SELECT COUNT(*) FROM public.cell_accessibility;")
            ).scalar_one()
        return int(count)

    def verify_metrics(self) -> AccessibilitySummary:
        """Return aggregate validation metrics for computed accessibility rows."""
        verify_sql = text(
            """
            SELECT
                COUNT(*)::integer AS total_cells,
                COUNT(*) FILTER (
                    WHERE avg_travel_time_to_shelter_seconds IS NOT NULL
                )::integer AS with_travel_time,
                COUNT(*) FILTER (
                    WHERE avg_road_density IS NOT NULL
                )::integer AS with_density,
                MIN(avg_travel_time_to_shelter_seconds)::integer AS min_seconds,
                MAX(avg_travel_time_to_shelter_seconds)::integer AS max_seconds
            FROM public.cell_accessibility;
            """
        )
        with self.engine.connect() as conn:
            row = conn.execute(verify_sql).mappings().one()
        return AccessibilitySummary(
            total_cells=int(row["total_cells"] or 0),
            with_travel_time=int(row["with_travel_time"] or 0),
            with_density=int(row["with_density"] or 0),
            min_seconds=row["min_seconds"],
            max_seconds=row["max_seconds"],
        )

    def export_handoff_csv(self, output_path: Path = DEFAULT_HANDOFF_PATH) -> Path:
        """Export accessibility rows to CSV for Member B readiness integration."""
        export_sql = text(
            """
            SELECT
                cell_id,
                avg_travel_time_to_shelter_seconds,
                avg_road_density,
                updated_at
            FROM public.cell_accessibility
            ORDER BY cell_id;
            """
        )
        with self.engine.connect() as conn:
            rows = conn.execute(export_sql).mappings().all()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", encoding="utf-8", newline="") as csv_file:
            writer = csv.DictWriter(
                csv_file,
                fieldnames=[
                    "cell_id",
                    "avg_travel_time_to_shelter_seconds",
                    "avg_road_density",
                    "updated_at",
                ],
            )
            writer.writeheader()
            for row in rows:
                writer.writerow(self._serialize_row(row))
        return output_path

    def _ensure_prerequisites(self) -> None:
        """Fail fast when required source tables or rows are missing."""
        precheck_sql = text(
            """
            SELECT
                (SELECT COUNT(*) FROM public.grid_cells) AS grid_cells_count,
                (SELECT COUNT(*) FROM public.shelters) AS shelters_count,
                (SELECT COUNT(*) FROM public.pj_roads) AS roads_count,
                (SELECT COUNT(*) FROM public.pj_roads_vertices_pgr) AS vertices_count;
            """
        )
        with self.engine.connect() as conn:
            counts = conn.execute(precheck_sql).mappings().one()
        if int(counts["grid_cells_count"] or 0) == 0:
            raise RuntimeError("grid_cells is empty; cannot compute accessibility")
        if int(counts["shelters_count"] or 0) == 0:
            raise RuntimeError("shelters is empty; cannot compute accessibility")
        if int(counts["roads_count"] or 0) == 0:
            raise RuntimeError("pj_roads is empty; cannot compute accessibility")
        if int(counts["vertices_count"] or 0) == 0:
            raise RuntimeError(
                "pj_roads_vertices_pgr is empty; refresh the materialized view first"
            )

    @staticmethod
    def _serialize_row(row: Any) -> dict[str, Any]:
        """Serialize DB mapping row into CSV-friendly field values."""
        return {
            "cell_id": row["cell_id"],
            "avg_travel_time_to_shelter_seconds": row[
                "avg_travel_time_to_shelter_seconds"
            ],
            "avg_road_density": row["avg_road_density"],
            "updated_at": (
                row["updated_at"].isoformat() if row.get("updated_at") else None
            ),
        }


def _parse_args() -> argparse.Namespace:
    """Parse command line arguments for direct module execution."""
    parser = argparse.ArgumentParser(
        description="Compute and export public.cell_accessibility metrics."
    )
    parser.add_argument(
        "--database-url",
        default=settings.database_url,
        help="PostgreSQL URL for routing/readiness database.",
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_HANDOFF_PATH),
        help="CSV output path for accessibility handoff.",
    )
    parser.add_argument(
        "--skip-export",
        action="store_true",
        help="Compute + verify only, skip CSV handoff export.",
    )
    return parser.parse_args()


def main() -> None:
    """Run compute, verification, and optional handoff export."""
    args = _parse_args()
    manager = AccessibilityManager(database_url=args.database_url)
    total_rows = manager.compute_accessibility()
    summary = manager.verify_metrics()
    print("Accessibility compute complete.")
    print(f"Rows in public.cell_accessibility: {total_rows}")
    print(f"Rows with travel-time metric: {summary.with_travel_time}")
    print(f"Rows with road-density metric: {summary.with_density}")
    if summary.min_seconds is not None and summary.max_seconds is not None:
        print(
            "Travel-time range (seconds): "
            f"{summary.min_seconds} to {summary.max_seconds}"
        )
    if not args.skip_export:
        output_path = manager.export_handoff_csv(Path(args.output))
        print(f"Handoff CSV written: {output_path}")


if __name__ == "__main__":
    main()
