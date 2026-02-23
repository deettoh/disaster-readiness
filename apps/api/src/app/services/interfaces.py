"""Service and repository interfaces."""

from typing import Protocol

from app.schemas.alerts import AlertListResponse
from app.schemas.hazards import HazardListResponse
from app.schemas.readiness import ReadinessListResponse
from app.schemas.reports import ReportCreateRequest, ReportCreateResponse
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

    async def enqueue_image_processing(self, report_id: str) -> str:
        """Enqueue report image-processing and return a job identifier."""
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
