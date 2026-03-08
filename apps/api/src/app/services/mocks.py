"""Mock implementations for unresolved integrations (B/C/D dependencies)."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

from app.core.exceptions import ExternalServiceError, NotFoundError
from app.schemas.alerts import AlertItem, AlertListResponse
from app.schemas.hazards import HazardItem, HazardListResponse
from app.schemas.readiness import ReadinessItem, ReadinessListResponse
from app.schemas.reports import (
    GeoPoint,
    ReportCreateRequest,
    ReportCreateResponse,
    ReportStatusResponse,
)
from app.schemas.routing import RouteRequest, RouteResponse
from app.schemas.weather import RainfallReading, WeatherSnapshotResponse


class MockReportRepository:
    """In-memory style mock for report persistence operations."""

    async def create_report(self, payload: ReportCreateRequest) -> ReportCreateResponse:
        """Return a mock report creation response."""
        _ = payload
        return ReportCreateResponse(
            report_id=uuid4(),
            status="processing",
            created_at=datetime.now(tz=UTC),
        )


class MockQueueClient:
    """Mock queue client for asynchronous processing jobs."""

    def __init__(self, fail_first_attempts: int = 0) -> None:
        """Initialize mock queue behavior and failure simulation settings."""
        self._fail_first_attempts = fail_first_attempts
        self._attempts = 0
        self.last_enqueued_payload: dict[str, str | None] | None = None

    @property
    def attempts(self) -> int:
        """Return current enqueue attempt count."""
        return self._attempts

    async def enqueue_image_processing(
        self,
        report_id: str,
        *,
        image_payload_b64: str | None = None,
        filename: str | None = None,
        content_type: str | None = None,
    ) -> str:
        """Return a deterministic mock job ID."""
        self._attempts += 1
        self.last_enqueued_payload = {
            "report_id": report_id,
            "image_payload_b64": image_payload_b64,
            "filename": filename,
            "content_type": content_type,
        }
        if self._attempts <= self._fail_first_attempts:
            raise ExternalServiceError(
                service="mock-queue",
                message="simulated enqueue failure",
                details={"attempt": self._attempts},
            )
        return f"mock-job-{report_id}"

    async def ping(self) -> bool:
        """Return mock queue connectivity status."""
        return True


class MockHazardService:
    """Mock hazard read service."""

    async def list_hazards(self) -> HazardListResponse:
        """Return a static hazard payload for integration scaffolding."""
        return HazardListResponse(
            items=[
                HazardItem(
                    report_id=uuid4(),
                    hazard_label="flooded_road",
                    confidence=0.81,
                    location=GeoPoint(latitude=3.139, longitude=101.6869),
                    redacted_image_url="https://example.local/redacted/mock.jpg",
                    observed_at=datetime.now(tz=UTC),
                )
            ]
        )


class MockReadinessService:
    """Mock readiness read service."""

    async def list_readiness(self) -> ReadinessListResponse:
        """Return a static readiness payload for integration scaffolding."""
        return ReadinessListResponse(
            items=[
                ReadinessItem(
                    cell_id="mock-cell-001",
                    score=72.5,
                    breakdown={
                        "baseline_vulnerability": 0.30,
                        "recent_hazards": 0.40,
                        "accessibility": 0.20,
                        "coverage_confidence": 0.10,
                    },
                    updated_at=datetime.now(tz=UTC),
                )
            ]
        )


class MockAlertService:
    """Mock alert read service."""

    async def list_alerts(self) -> AlertListResponse:
        """Return a static alert payload for integration scaffolding."""
        return AlertListResponse(
            items=[
                AlertItem(
                    alert_id=uuid4(),
                    level="high",
                    message="High flood risk detected in nearby cell",
                    cell_id="mock-cell-001",
                    created_at=datetime.now(tz=UTC),
                )
            ]
        )


class MockRoutingService:
    """Mock routing service."""

    async def compute_route(self, payload: RouteRequest) -> RouteResponse:
        """Return a simple synthetic line route for the request payload."""
        destination = payload.destination or GeoPoint(
            latitude=payload.origin.latitude + 0.002,
            longitude=payload.origin.longitude + 0.002,
        )
        geometry = {
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "LineString",
                        "coordinates": [
                            [payload.origin.longitude, payload.origin.latitude],
                            [destination.longitude, destination.latitude],
                        ],
                    },
                    "properties": {"mode": "evacuation"},
                }
            ],
        }
        return RouteResponse(
            route_geojson=geometry, distance_meters=500.0, eta_minutes=7.5
        )


class MockReportStatusStore:
    """In-memory status store for report processing lifecycle."""

    def __init__(self) -> None:
        """Initialize in-memory storage."""
        self._status_by_report: dict[str, ReportStatusResponse] = {}

    async def mark_processing(
        self,
        report_id: UUID,
        *,
        job_id: str,
        attempt_count: int,
    ) -> ReportStatusResponse:
        """Mark report status as processing."""
        status = ReportStatusResponse(
            report_id=report_id,
            status="processing",
            job_id=job_id,
            attempt_count=attempt_count,
            updated_at=datetime.now(tz=UTC),
        )
        self._status_by_report[str(report_id)] = status
        return status

    async def mark_complete(self, report_id: UUID) -> ReportStatusResponse:
        """Mark report status as complete."""
        existing = self._status_by_report.get(str(report_id))
        status = ReportStatusResponse(
            report_id=report_id,
            status="complete",
            job_id=existing.job_id if existing else None,
            attempt_count=existing.attempt_count if existing else 0,
            updated_at=datetime.now(tz=UTC),
        )
        self._status_by_report[str(report_id)] = status
        return status

    async def mark_failed(
        self,
        report_id: UUID,
        *,
        error: str,
        attempt_count: int | None = None,
    ) -> ReportStatusResponse:
        """Mark report status as failed."""
        existing = self._status_by_report.get(str(report_id))
        status = ReportStatusResponse(
            report_id=report_id,
            status="failed",
            job_id=existing.job_id if existing else None,
            error=error,
            attempt_count=(
                attempt_count
                if attempt_count is not None
                else (existing.attempt_count if existing else 0)
            ),
            updated_at=datetime.now(tz=UTC),
        )
        self._status_by_report[str(report_id)] = status
        return status

    async def get_status(self, report_id: UUID) -> ReportStatusResponse:
        """Return report status if present."""
        status = self._status_by_report.get(str(report_id))
        if status is None:
            raise NotFoundError(resource="report_status", resource_id=report_id)
        return status


class MockPostProcessingHooks:
    """Mock implementation of post-processing downstream trigger hooks."""

    def __init__(self) -> None:
        """Initialize trigger call capture."""
        self.trigger_calls: dict[str, list[str]] = {
            "road_penalty_update": [],
            "readiness_recompute": [],
            "alert_generation": [],
        }

    async def trigger_road_penalty_update(self, report_id: UUID) -> None:
        """Capture road penalty trigger invocation."""
        self.trigger_calls["road_penalty_update"].append(str(report_id))

    async def trigger_readiness_recompute(self, report_id: UUID) -> None:
        """Capture readiness recompute trigger invocation."""
        self.trigger_calls["readiness_recompute"].append(str(report_id))

    async def trigger_alert_generation(self, report_id: UUID) -> None:
        """Capture alert generation trigger invocation."""
        self.trigger_calls["alert_generation"].append(str(report_id))

    def snapshot(self) -> dict[str, list[str]]:
        """Return captured trigger calls."""
        return {name: calls[:] for name, calls in self.trigger_calls.items()}


class MockWeatherService:
    """Mock weather service returning synthetic rainfall data."""

    async def get_weather_snapshot(self) -> WeatherSnapshotResponse:
        """Return static weather readings for integration scaffolding."""
        now = datetime.now(tz=UTC)
        return WeatherSnapshotResponse(
            readings=[
                RainfallReading(
                    neighbourhood="PJU 5",
                    lat=3.1711,
                    lng=101.5805,
                    precipitation_mm=2.4,
                    temperature_c=29.1,
                    relative_humidity=78.0,
                    weather_code=61,
                    timestamp=now,
                ),
                RainfallReading(
                    neighbourhood="SS 2",
                    lat=3.1163,
                    lng=101.6190,
                    precipitation_mm=0.0,
                    temperature_c=31.2,
                    relative_humidity=65.0,
                    weather_code=3,
                    timestamp=now,
                ),
                RainfallReading(
                    neighbourhood="Seksyen 13",
                    lat=3.1149,
                    lng=101.6375,
                    precipitation_mm=5.1,
                    temperature_c=27.8,
                    relative_humidity=88.0,
                    weather_code=63,
                    timestamp=now,
                ),
            ],
            fetched_at=now,
        )
