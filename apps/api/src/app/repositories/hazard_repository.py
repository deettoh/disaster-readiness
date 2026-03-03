"""ORM-backed hazard query repository."""

from __future__ import annotations

from asyncio import to_thread

from geoalchemy2 import Geometry
from sqlalchemy import cast, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import ExternalServiceError
from app.db.models import Image, Report
from app.repositories.base import _ORMRepositoryBase
from app.schemas.hazards import HazardItem, HazardListResponse
from app.schemas.reports import GeoPoint


class SQLHazardRepository(_ORMRepositoryBase):
    """Hazard read repository backed by SQLAlchemy ORM queries."""

    def __init__(
        self,
        *,
        database_url: str,
        engine: Engine | None = None,
        max_rows: int = 500,
    ) -> None:
        """Initialize hazard repository settings."""
        super().__init__(database_url=database_url, engine=engine)
        self._max_rows = max_rows

    async def list_hazards(self) -> HazardListResponse:
        """Return hazard items from report records."""
        return await to_thread(self._list_hazards_sync)

    def _list_hazards_sync(self) -> HazardListResponse:
        """Run blocking ORM query for hazard payload."""
        latest_image_path = (
            select(Image.bucket_path)
            .where(Image.report_id == Report.id)
            .order_by(Image.uploaded_at.desc())
            .limit(1)
            .scalar_subquery()
        )
        point_geom = cast(Report.geom, Geometry(geometry_type="POINT", srid=4326))

        stmt = (
            select(
                Report.id.label("report_id"),
                func.coalesce(func.nullif(Report.hazard_type, ""), "unknown").label(
                    "hazard_label"
                ),
                func.least(func.greatest(func.coalesce(Report.confidence, 0), 0), 1).label(
                    "confidence"
                ),
                func.ST_Y(point_geom).label("latitude"),
                func.ST_X(point_geom).label("longitude"),
                latest_image_path.label("redacted_image_url"),
                Report.created_at.label("observed_at"),
            )
            .where(Report.geom.is_not(None))
            .order_by(Report.created_at.desc())
            .limit(self._max_rows)
        )

        with self._session_factory() as session:
            try:
                rows = session.execute(stmt).mappings().all()
            except SQLAlchemyError as exc:
                raise ExternalServiceError(
                    service="data-db",
                    message="failed to query hazards",
                    details={
                        "operation": "list_hazards",
                        "database_url": self._database_url,
                    },
                ) from exc

        items: list[HazardItem] = []
        for row in rows:
            latitude = row.get("latitude")
            longitude = row.get("longitude")
            observed_at = row.get("observed_at")
            if latitude is None or longitude is None or observed_at is None:
                continue

            confidence = min(max(float(row.get("confidence", 0.0)), 0.0), 1.0)
            image_url = row.get("redacted_image_url")

            items.append(
                HazardItem(
                    report_id=row["report_id"],
                    hazard_label=str(row.get("hazard_label") or "unknown"),
                    confidence=confidence,
                    location=GeoPoint(latitude=float(latitude), longitude=float(longitude)),
                    redacted_image_url=str(image_url) if image_url is not None else None,
                    observed_at=observed_at,
                )
            )

        return HazardListResponse(items=items)
