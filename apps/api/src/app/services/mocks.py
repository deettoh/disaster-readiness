"""Mock implementations for unresolved integrations (B/C/D dependencies)."""

from datetime import UTC, datetime
from uuid import uuid4

from app.schemas.alerts import AlertItem, AlertListResponse
from app.schemas.hazards import HazardItem, HazardListResponse
from app.schemas.readiness import ReadinessItem, ReadinessListResponse
from app.schemas.reports import GeoPoint, ReportCreateRequest, ReportCreateResponse
from app.schemas.routing import RouteRequest, RouteResponse


class MockReportRepository:
    """In-memory-style mock for report persistence operations."""

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

    async def enqueue_image_processing(self, report_id: str) -> str:
        """Return a deterministic mock job ID."""
        return f"mock-job-{report_id}"


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
        return RouteResponse(route_geojson=geometry, distance_meters=500.0, eta_minutes=7.5)
