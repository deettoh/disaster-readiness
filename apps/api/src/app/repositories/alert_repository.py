"""ORM-backed alert query repository."""

from __future__ import annotations

from asyncio import to_thread

from sqlalchemy import func, select
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import ExternalServiceError
from app.db.models import Alert, GridCell
from app.repositories.base import _ORMRepositoryBase
from app.schemas.alerts import AlertItem, AlertListResponse


class SQLAlertRepository(_ORMRepositoryBase):
    """Alert repository backed by SQLAlchemy ORM queries."""

    def __init__(
        self,
        *,
        database_url: str,
        engine: Engine | None = None,
        max_rows: int = 500,
    ) -> None:
        """Initialize alert repository settings."""
        super().__init__(database_url=database_url, engine=engine)
        self._max_rows = max_rows

    async def list_alerts(self) -> AlertListResponse:
        """Return alerts from SQL storage."""
        return await to_thread(self._list_alerts_sync)

    def _list_alerts_sync(self) -> AlertListResponse:
        """Run blocking ORM query for alert payload."""
        stmt = (
            select(
                Alert.id.label("alert_id"),
                func.coalesce(func.nullif(Alert.severity, ""), "medium").label("level"),
                func.coalesce(Alert.message, "").label("message"),
                GridCell.cell_id.label("grid_cell_id"),
                Alert.cell_id.label("fallback_cell_id"),
                Alert.triggered_at.label("created_at"),
            )
            .select_from(Alert)
            .join(GridCell, GridCell.id == Alert.cell_id, isouter=True)
            .order_by(Alert.triggered_at.desc())
            .limit(self._max_rows)
        )

        with self._session_factory() as session:
            try:
                rows = session.execute(stmt).mappings().all()
            except SQLAlchemyError as exc:
                raise ExternalServiceError(
                    service="data-db",
                    message="failed to query alerts",
                    details={
                        "operation": "list_alerts",
                        "database_url": self._database_url,
                    },
                ) from exc

        items: list[AlertItem] = []
        for row in rows:
            created_at = row.get("created_at")
            cell_id = str(row.get("grid_cell_id") or row.get("fallback_cell_id") or "")
            if created_at is None or not cell_id:
                continue

            items.append(
                AlertItem(
                    alert_id=row["alert_id"],
                    level=str(row.get("level") or "medium"),
                    message=str(row.get("message") or ""),
                    cell_id=cell_id,
                    created_at=created_at,
                )
            )

        return AlertListResponse(items=items)
