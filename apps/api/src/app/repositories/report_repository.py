"""ORM-backed report repository."""

from __future__ import annotations

from asyncio import to_thread
from typing import Any

from geoalchemy2.elements import WKTElement
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import ExternalServiceError
from app.db.models import Report
from app.repositories.base import _ORMRepositoryBase
from app.schemas.reports import ReportCreateRequest, ReportCreateResponse


class SQLReportRepository(_ORMRepositoryBase):
    """Report repository implementation backed by SQLAlchemy ORM."""

    def __init__(
        self,
        *,
        database_url: str,
        engine: Engine | None = None,
    ) -> None:
        """Initialize report repository settings."""
        super().__init__(database_url=database_url, engine=engine)

    async def create_report(self, payload: ReportCreateRequest) -> ReportCreateResponse:
        """Create report metadata in SQL database."""
        return await to_thread(self._create_report_sync, payload)

    def _create_report_sync(self, payload: ReportCreateRequest) -> ReportCreateResponse:
        """Run blocking ORM insert for report metadata."""
        metadata: dict[str, Any] = {}
        if payload.note:
            metadata["note"] = payload.note
        if payload.user_hazard_label:
            metadata["user_hazard_label"] = payload.user_hazard_label

        report = Report(
            geom=WKTElement(
                f"POINT({payload.location.longitude} {payload.location.latitude})",
                srid=4326,
            ),
            hazard_type=payload.user_hazard_label,
            source="web_report",
            metadata_json=metadata or None,
        )

        with self._session_factory() as session:
            try:
                session.add(report)
                session.flush()
                session.refresh(report)
                session.commit()
            except SQLAlchemyError as exc:
                session.rollback()
                raise ExternalServiceError(
                    service="data-db",
                    message="failed to create report",
                    details={
                        "operation": "create_report",
                        "database_url": self._database_url,
                    },
                ) from exc

        return ReportCreateResponse(
            report_id=report.id,
            status="processing",
            created_at=report.created_at,
        )
