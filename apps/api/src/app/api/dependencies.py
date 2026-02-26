"""Dependency providers for repositories/services."""

from app.core.config import get_settings
from app.services.interfaces import (
    AlertQueryService,
    HazardQueryService,
    PostProcessingHooks,
    QueueClient,
    ReadinessQueryService,
    ReportRepository,
    ReportStatusStore,
    RoutingService,
)
from app.services.mocks import (
    MockAlertService,
    MockHazardService,
    MockPostProcessingHooks,
    MockQueueClient,
    MockReadinessService,
    MockReportRepository,
    MockReportStatusStore,
    MockRoutingService,
)
from app.services.orchestration import ReportOrchestrationService
from app.services.queue_backends import RQQueueClient

_report_repo = MockReportRepository()
_mock_queue_client = MockQueueClient()
_hazard_service = MockHazardService()
_readiness_service = MockReadinessService()
_alert_service = MockAlertService()
_routing_service = MockRoutingService()
_status_store = MockReportStatusStore()
_post_processing_hooks = MockPostProcessingHooks()
_rq_queue_client: RQQueueClient | None = None
_orchestration_service: ReportOrchestrationService | None = None


def get_report_repository() -> ReportRepository:
    """Return the report repository dependency."""
    return _report_repo


def get_queue_client() -> QueueClient:
    """Return the queue client dependency."""
    settings = get_settings()
    if settings.queue_backend == "mock":
        return _mock_queue_client

    global _rq_queue_client
    if _rq_queue_client is None:
        _rq_queue_client = RQQueueClient(
            redis_url=settings.redis_url,
            queue_name=settings.queue_name,
            default_timeout=settings.queue_default_timeout,
            retry_max=settings.queue_retry_max,
            retry_intervals=settings.queue_retry_intervals,
        )
    return _rq_queue_client


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


def get_report_status_store() -> ReportStatusStore:
    """Return the report status store dependency."""
    return _status_store


def get_post_processing_hooks() -> PostProcessingHooks:
    """Return the post-processing hooks dependency."""
    return _post_processing_hooks


def get_orchestration_service() -> ReportOrchestrationService:
    """Return report orchestration service dependency."""
    settings = get_settings()
    global _orchestration_service
    if _orchestration_service is None:
        _orchestration_service = ReportOrchestrationService(
            queue_client=get_queue_client(),
            status_store=get_report_status_store(),
            post_processing_hooks=get_post_processing_hooks(),
            enqueue_max_attempts=settings.queue_enqueue_max_attempts,
            enqueue_backoff_seconds=settings.queue_enqueue_backoff_seconds,
        )
    return _orchestration_service
