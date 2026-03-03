"""Service and repository interfaces."""

from typing import Protocol
from uuid import UUID

from app.schemas.alerts import AlertListResponse
from app.schemas.hazards import HazardListResponse
from app.schemas.readiness import ReadinessListResponse
from app.schemas.reports import (
    ReportCreateRequest,
    ReportCreateResponse,
    ReportStatusResponse,
)
from app.schemas.routing import RouteRequest, RouteResponse


# Need Member B
class ReportRepository(Protocol):
    """Persistence interface for report metadata."""

    async def create_report(self, payload: ReportCreateRequest) -> ReportCreateResponse:
        """Create a report record and return report metadata."""
        ...


# Need member D
class QueueClient(Protocol):
    """Queue interface for background jobs."""

    async def enqueue_image_processing(
        self,
        report_id: str,
        *,
        image_payload_b64: str | None = None,
        filename: str | None = None,
        content_type: str | None = None,
    ) -> str:
        """Enqueue report image-processing and return a job identifier."""
        ...

    async def ping(self) -> bool:
        """Check queue backend connectivity."""
        ...


# Need member B and D
class HazardQueryService(Protocol):
    """Read interface for hazard map/list data."""

    async def list_hazards(self) -> HazardListResponse:
        """Return hazard items for the current query context."""
        ...


# Need member B/C/D
class ReadinessQueryService(Protocol):
    """Read interface for readiness score data."""

    async def list_readiness(self) -> ReadinessListResponse:
        """Return readiness score items for the current query context."""
        ...


# Need member C
class AlertQueryService(Protocol):
    """Read interface for alert data."""

    async def list_alerts(self) -> AlertListResponse:
        """Return current alert items for the current query context."""
        ...


class RoutingService(Protocol):
    """Routing interface for evacuation route computation."""

    async def compute_route(self, payload: RouteRequest) -> RouteResponse:
        """Compute and return a route response for the given request."""
        ...


class ReportStatusStore(Protocol):
    """Persistence interface for report processing lifecycle state."""

    async def mark_processing(
        self,
        report_id: UUID,
        *,
        job_id: str,
        attempt_count: int,
    ) -> ReportStatusResponse:
        """Mark report as processing with queue metadata."""
        ...

    async def mark_complete(self, report_id: UUID) -> ReportStatusResponse:
        """Mark report processing as complete."""
        ...

    async def mark_failed(
        self,
        report_id: UUID,
        *,
        error: str,
        attempt_count: int | None = None,
    ) -> ReportStatusResponse:
        """Mark report processing as failed with error context."""
        ...

    async def get_status(self, report_id: UUID) -> ReportStatusResponse:
        """Return the latest report processing status."""
        ...


class PostProcessingHooks(Protocol):
    """Integration hooks triggered when prediction processing completes."""

    async def trigger_road_penalty_update(self, report_id: UUID) -> None:
        """Trigger downstream road risk penalty updates."""
        ...

    async def trigger_readiness_recompute(self, report_id: UUID) -> None:
        """Trigger readiness recomputation for impacted cells."""
        ...

    async def trigger_alert_generation(self, report_id: UUID) -> None:
        """Trigger alert generation for impacted areas."""
        ...
