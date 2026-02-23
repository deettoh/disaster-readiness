"""Dependency providers for repositories/services."""

from app.services.interfaces import (
    AlertQueryService,
    HazardQueryService,
    QueueClient,
    ReadinessQueryService,
    ReportRepository,
    RoutingService,
)
from app.services.mocks import (
    MockAlertService,
    MockHazardService,
    MockQueueClient,
    MockReadinessService,
    MockReportRepository,
    MockRoutingService,
)

_report_repo = MockReportRepository()
_queue_client = MockQueueClient()
_hazard_service = MockHazardService()
_readiness_service = MockReadinessService()
_alert_service = MockAlertService()
_routing_service = MockRoutingService()


def get_report_repository() -> ReportRepository:
    """Return the report repository dependency."""
    return _report_repo


def get_queue_client() -> QueueClient:
    """Return the queue client dependency."""
    return _queue_client


def get_hazard_service() -> HazardQueryService:
    """Return the hazard query dependency."""
    return _hazard_service


def get_readiness_service() -> ReadinessQueryService:
    """Return the readiness query dependency."""
    return _readiness_service


def get_alert_service() -> AlertQueryService:
    """Return the alert query dependency."""
    return _alert_service


def get_routing_service() -> RoutingService:
    """Return the routing service dependency."""
    return _routing_service
