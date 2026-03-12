"""SQL backed post processing hooks for readiness recompute and alerts."""

from __future__ import annotations

import logging
from asyncio import to_thread
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class SQLPostProcessingHooks:
    """Post processing hooks that call readiness engine DB functions.

    Triggered after image processing completes for a report.
    Each hook resolves the affected grid cell from the report geometry,
    then delegates to the corresponding Postgres function.
    """

    def __init__(
        self,
        *,
        database_url: str,
        engine: Engine | None = None,
        road_penalty_radius_m: float = 500.0,
        road_penalty_weight: float = 50.0,
        readiness_alert_threshold: float = 40.0,
    ) -> None:
        """Initialize with DB connection and tuning parameters."""
        self._database_url = database_url
        self._engine = engine or create_engine(database_url)
        self._road_penalty_radius_m = road_penalty_radius_m
        self._road_penalty_weight = road_penalty_weight
        self._readiness_alert_threshold = readiness_alert_threshold

    async def trigger_road_penalty_update(self, report_id: UUID) -> None:
        """Update risk penalties on roads near the report location."""
        await to_thread(self._road_penalty_update_sync, report_id)

    async def trigger_readiness_recompute(self, report_id: UUID) -> None:
        """Recompute readiness score for the cell containing the report."""
        await to_thread(self._readiness_recompute_sync, report_id)

    async def trigger_alert_generation(self, report_id: UUID) -> None:
        """Generate alerts for low readiness and severe hazards."""
        await to_thread(self._alert_generation_sync, report_id)

    # Synchronous implementations, run via to_thread

    def _get_report_coords(self, report_id: UUID) -> tuple[float, float] | None:
        """Return (lng, lat) from report geometry, or None if not found."""
        sql = text("""
            SELECT
                extensions.ST_X(r.geom::extensions.geometry) AS lng,
                extensions.ST_Y(r.geom::extensions.geometry) AS lat
            FROM public.reports AS r
            WHERE r.id = :report_id
        """)
        with self._engine.connect() as conn:
            row = conn.execute(sql, {"report_id": report_id}).mappings().first()
        if row is None:
            logger.warning("Report %s not found for post-processing", report_id)
            return None
        return (float(row["lng"]), float(row["lat"]))

    def _get_cell_id(self, lng: float, lat: float) -> int | None:
        """Resolve grid cell ID from coordinates."""
        sql = text("SELECT public.point_to_cell(:lng, :lat) AS cell_id")
        with self._engine.connect() as conn:
            row = conn.execute(sql, {"lng": lng, "lat": lat}).mappings().first()
        if row is None or row["cell_id"] is None:
            logger.warning("No grid cell found for (%.6f, %.6f)", lng, lat)
            return None
        return int(row["cell_id"])

    def _get_latest_prediction_id(self, report_id: UUID) -> str | None:
        """Return the most recent hazard_prediction ID linked to a report's geom."""
        sql = text("""
            SELECT hp.id
            FROM public.hazard_predictions AS hp
            JOIN public.reports AS r ON extensions.ST_DWithin(
                hp.geom,
                r.geom,
                0.001
            )
            WHERE r.id = :report_id
            ORDER BY hp.created_at DESC
            LIMIT 1
        """)
        with self._engine.connect() as conn:
            row = conn.execute(sql, {"report_id": report_id}).mappings().first()
        if row is None:
            return None
        return str(row["id"])

    def _road_penalty_update_sync(self, report_id: UUID) -> None:
        """Apply risk penalties to nearby roads from latest hazard prediction."""
        coords = self._get_report_coords(report_id)
        if coords is None:
            return
        lng, lat = coords

        # Find latest prediction probability for penalty scaling
        prob_sql = text("""
            SELECT hp.probability
            FROM public.hazard_predictions AS hp
            JOIN public.reports AS r ON extensions.ST_DWithin(
                hp.geom, r.geom, 0.001
            )
            WHERE r.id = :report_id
            ORDER BY hp.created_at DESC
            LIMIT 1
        """)
        update_sql = text("""
            UPDATE public.roads_edges
            SET cost = cost + (:penalty_weight * :probability)
            WHERE id IN (
                SELECT edge_id
                FROM public.roads_near_hazard(:lng, :lat, :radius_m)
            )
        """)

        try:
            with self._engine.begin() as conn:
                prob_row = (
                    conn.execute(prob_sql, {"report_id": report_id}).mappings().first()
                )
                probability = float(prob_row["probability"]) if prob_row else 0.5

                result = conn.execute(
                    update_sql,
                    {
                        "penalty_weight": self._road_penalty_weight,
                        "probability": probability,
                        "lng": lng,
                        "lat": lat,
                        "radius_m": self._road_penalty_radius_m,
                    },
                )
                logger.info(
                    "Updated road penalties for report %s: %d edges affected",
                    report_id,
                    result.rowcount,
                )
        except SQLAlchemyError:
            logger.exception("Failed to update road penalties for report %s", report_id)

    def _readiness_recompute_sync(self, report_id: UUID) -> None:
        """Recompute readiness score for the cell containing the report."""
        coords = self._get_report_coords(report_id)
        if coords is None:
            return
        lng, lat = coords
        cell_id = self._get_cell_id(lng, lat)
        if cell_id is None:
            return

        sql = text("SELECT public.update_readiness_scores(:cell_id)")
        try:
            with self._engine.begin() as conn:
                conn.execute(sql, {"cell_id": cell_id})
            logger.info(
                "Recomputed readiness for cell %d (report %s)", cell_id, report_id
            )
        except SQLAlchemyError:
            logger.exception(
                "Failed to recompute readiness for cell %d (report %s)",
                cell_id,
                report_id,
            )

    def _alert_generation_sync(self, report_id: UUID) -> None:
        """Generate alerts for low readiness and severe hazards."""
        coords = self._get_report_coords(report_id)
        if coords is None:
            return
        lng, lat = coords
        cell_id = self._get_cell_id(lng, lat)
        if cell_id is None:
            return

        low_readiness_sql = text(
            "SELECT public.raise_alert_if_low_readiness(:cell_id, :threshold)"
        )
        prediction_id = self._get_latest_prediction_id(report_id)
        severe_sql = text(
            "SELECT public.raise_alert_for_severe_hazard(:prediction_id, :cell_id)"
        )

        try:
            with self._engine.begin() as conn:
                conn.execute(
                    low_readiness_sql,
                    {
                        "cell_id": cell_id,
                        "threshold": self._readiness_alert_threshold,
                    },
                )
                if prediction_id is not None:
                    conn.execute(
                        severe_sql,
                        {"prediction_id": prediction_id, "cell_id": cell_id},
                    )
            logger.info(
                "Alert generation completed for cell %d (report %s)",
                cell_id,
                report_id,
            )
        except SQLAlchemyError:
            logger.exception(
                "Failed alert generation for cell %d (report %s)",
                cell_id,
                report_id,
            )
