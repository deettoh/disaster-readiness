"""ORM-backed readiness query repository."""

from __future__ import annotations

from asyncio import to_thread

from sqlalchemy import select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import ExternalServiceError
from app.db.models import GridCell, ReadinessScore
from app.repositories.base import _ORMRepositoryBase
from app.schemas.readiness import ReadinessItem, ReadinessListResponse


class SQLReadinessRepository(_ORMRepositoryBase):
    """Readiness score repository backed by SQLAlchemy ORM queries."""

    def __init__(
        self,
        *,
        database_url: str,
        engine: Engine | None = None,
        max_rows: int = 500,
    ) -> None:
        """Initialize readiness repository settings."""
        super().__init__(database_url=database_url, engine=engine)
        self._max_rows = max_rows

    async def list_readiness(self) -> ReadinessListResponse:
        """Return readiness scores from SQL storage."""
        return await to_thread(self._list_readiness_sync)

    def _list_readiness_sync(self) -> ReadinessListResponse:
        """Run blocking ORM query and aggregate readiness payloads by neighborhood."""
        stmt = (
            select(
                GridCell.neighborhood.label("neighborhood"),
                GridCell.cell_id.label("grid_cell_id"),
                ReadinessScore.cell_id.label("fallback_cell_id"),
                ReadinessScore.score.label("score"),
                ReadinessScore.breakdown.label("breakdown"),
                ReadinessScore.updated_at.label("updated_at"),
            )
            .select_from(ReadinessScore)
            .join(GridCell, GridCell.id == ReadinessScore.cell_id, isouter=True)
            .order_by(ReadinessScore.updated_at.desc())
        )

        with self._session_factory() as session:
            try:
                rows = session.execute(stmt).mappings().all()
            except SQLAlchemyError as exc:
                raise ExternalServiceError(
                    service="data-db",
                    message="failed to query readiness scores",
                    details={
                        "operation": "list_readiness",
                        "database_url": self._database_url,
                    },
                ) from exc

        neighborhood_groups = {}
        for row in rows:
            updated_at = row.get("updated_at")
            if updated_at is None:
                continue

            group_key = str(
                row.get("neighborhood")
                or row.get("grid_cell_id")
                or row.get("fallback_cell_id")
                or ""
            )
            if not group_key:
                continue

            score = min(max(float(row.get("score", 0.0)), 0.0), 100.0)

            breakdown_raw = row.get("breakdown")
            breakdown = (
                dict(breakdown_raw)
                if isinstance(breakdown_raw, dict)
                else {"raw_breakdown": breakdown_raw}
            )

            if group_key not in neighborhood_groups:
                neighborhood_groups[group_key] = {
                    "scores": [],
                    "breakdowns": [],
                    "updated_ats": [],
                }

            neighborhood_groups[group_key]["scores"].append(score)
            neighborhood_groups[group_key]["breakdowns"].append(breakdown)
            neighborhood_groups[group_key]["updated_ats"].append(updated_at)

        items: list[ReadinessItem] = []
        for group_key, data in neighborhood_groups.items():
            avg_score = sum(data["scores"]) / len(data["scores"])

            aggregated_breakdown = {}
            # Based on readiness engine
            numeric_keys = [
                "hazard_penalty",
                "vulnerability_penalty",
                "accessibility_bonus",
                "confidence_bonus",
            ]

            for key in numeric_keys:
                values = [
                    bd.get(key, 0)
                    for bd in data["breakdowns"]
                    if isinstance(bd.get(key), int | float)
                ]
                if values:
                    aggregated_breakdown[key] = sum(values) / len(values)
                else:
                    aggregated_breakdown[key] = 0.0

            latest_updated_at = max(data["updated_ats"])

            items.append(
                ReadinessItem(
                    cell_id=group_key,  # API expects cell_id, we map it to neighborhood
                    score=avg_score,
                    breakdown=aggregated_breakdown,
                    updated_at=latest_updated_at,
                )
            )

        return ReadinessListResponse(items=items)
