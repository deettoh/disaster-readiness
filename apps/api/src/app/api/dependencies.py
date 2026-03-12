"""Dependency providers for repositories/services."""

from fastapi import Depends, Request

from app.core.config import Settings, get_settings
from app.core.exceptions import RateLimitExceededError
from app.core.rate_limit import InMemoryRateLimiter
from app.repositories.alert_repository import SQLAlertRepository
from app.repositories.hazard_repository import SQLHazardRepository
from app.repositories.readiness_repository import SQLReadinessRepository
from app.repositories.report_repository import SQLReportRepository
from app.services.interfaces import (
    AlertQueryService,
    HazardQueryService,
    PostProcessingHooks,
    QueueClient,
    ReadinessQueryService,
    ReportRepository,
    ReportStatusStore,
    RoutingService,
    WeatherQueryService,
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
    MockWeatherService,
)
from app.services.orchestration import ReportOrchestrationService
from app.services.post_processing_sql import SQLPostProcessingHooks
from app.services.queue_backends import InProcessQueueClient
from app.services.routing_sql import SQLRoutingService
from app.services.weather_service import WeatherService

_report_repo = MockReportRepository()
_mock_queue_client = MockQueueClient()
_hazard_service = MockHazardService()
_readiness_service = MockReadinessService()
_alert_service = MockAlertService()
_mock_routing_service = MockRoutingService()
_sql_report_repository: SQLReportRepository | None = None
_sql_hazard_service: SQLHazardRepository | None = None
_sql_readiness_service: SQLReadinessRepository | None = None
_sql_alert_service: SQLAlertRepository | None = None
_sql_routing_service: SQLRoutingService | None = None
_status_store = MockReportStatusStore()
_post_processing_hooks = MockPostProcessingHooks()
_sql_post_processing_hooks: SQLPostProcessingHooks | None = None
_mock_weather_service = MockWeatherService()
_live_weather_service: WeatherService | None = None
_in_process_queue_client: InProcessQueueClient | None = None
_orchestration_service: ReportOrchestrationService | None = None
_rate_limiter = InMemoryRateLimiter()


def _get_client_identity(request: Request) -> str:
    """Return client identity for per-client throttling."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()  # Original client IP from header
    if request.client is not None:
        return request.client.host  # Load balancer IP
    return "unknown"


def get_report_repository() -> ReportRepository:
    """Return the report repository dependency."""
    settings = get_settings()
    if settings.data_backend == "mock":
        return _report_repo

    global _sql_report_repository
    if _sql_report_repository is None:
        _sql_report_repository = SQLReportRepository(database_url=settings.database_url)
    return _sql_report_repository


def get_queue_client() -> QueueClient:
    """Return the queue client dependency."""
    settings = get_settings()
    if settings.queue_backend == "mock":
        return _mock_queue_client

    global _in_process_queue_client
    if _in_process_queue_client is None:
        _in_process_queue_client = InProcessQueueClient(
            status_store=get_report_status_store(),
            post_processing_hooks=get_post_processing_hooks(),
            database_url=settings.database_url,
            supabase_url=settings.supabase_url,
            supabase_key=settings.supabase_secret_key,
            model_version=settings.image_processing_model_version,
        )
    return _in_process_queue_client


def get_hazard_service() -> HazardQueryService:
    """Return the hazard query dependency."""
    settings = get_settings()
    if settings.data_backend == "mock":
        return _hazard_service

    global _sql_hazard_service
    if _sql_hazard_service is None:
        _sql_hazard_service = SQLHazardRepository(database_url=settings.database_url)
    return _sql_hazard_service


def get_readiness_service() -> ReadinessQueryService:
    """Return the readiness query dependency."""
    settings = get_settings()
    if settings.data_backend == "mock":
        return _readiness_service

    global _sql_readiness_service
    if _sql_readiness_service is None:
        _sql_readiness_service = SQLReadinessRepository(
            database_url=settings.database_url
        )
    return _sql_readiness_service


def get_alert_service() -> AlertQueryService:
    """Return the alert query dependency."""
    settings = get_settings()
    if settings.data_backend == "mock":
        return _alert_service

    global _sql_alert_service
    if _sql_alert_service is None:
        _sql_alert_service = SQLAlertRepository(database_url=settings.database_url)
    return _sql_alert_service


def get_routing_service() -> RoutingService:
    """Return the routing service dependency."""
    settings = get_settings()
    if settings.routing_backend == "mock":
        return _mock_routing_service

    global _sql_routing_service
    if _sql_routing_service is None:
        _sql_routing_service = SQLRoutingService(
            database_url=settings.database_url,
            algorithm=settings.routing_algorithm,
        )
    return _sql_routing_service


def get_report_status_store() -> ReportStatusStore:
    """Return the report status store dependency."""
    return _status_store


def get_post_processing_hooks() -> PostProcessingHooks:
    """Return the post-processing hooks dependency."""
    settings = get_settings()
    if settings.data_backend == "mock":
        return _post_processing_hooks

    global _sql_post_processing_hooks
    if _sql_post_processing_hooks is None:
        _sql_post_processing_hooks = SQLPostProcessingHooks(
            database_url=settings.database_url,
            road_penalty_radius_m=settings.road_penalty_radius_m,
            road_penalty_weight=settings.road_penalty_weight,
            readiness_alert_threshold=settings.readiness_alert_threshold,
        )
    return _sql_post_processing_hooks


def get_weather_service() -> WeatherQueryService:
    """Return the weather service dependency."""
    settings = get_settings()
    if settings.weather_backend == "mock":
        return _mock_weather_service

    global _live_weather_service
    if _live_weather_service is None:
        _live_weather_service = WeatherService()
    return _live_weather_service


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


def enforce_report_create_rate_limit(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> None:
    """Enforce anti-spam throttle for report creation requests."""
    client = _get_client_identity(request)
    allowed, retry_after = _rate_limiter.consume(
        key=f"reports:create:{client}",
        max_requests=settings.rate_limit_reports_per_minute,
        window_seconds=60,
    )
    if not allowed:
        raise RateLimitExceededError(
            message="Too many report creation requests. Please retry later.",
            retry_after_seconds=retry_after,
            details={"endpoint": "/reports"},
        )


def enforce_report_image_rate_limit(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> None:
    """Enforce anti-spam throttle for report image upload requests."""
    client = _get_client_identity(request)
    allowed, retry_after = _rate_limiter.consume(
        key=f"reports:image:{client}",
        max_requests=settings.rate_limit_report_images_per_minute,
        window_seconds=60,
    )
    if not allowed:
        raise RateLimitExceededError(
            message="Too many report image uploads. Please retry later.",
            retry_after_seconds=retry_after,
            details={"endpoint": "/reports/{report_id}/image"},
        )


def reset_rate_limiter_state() -> None:
    """Reset rate limiter state for test isolation."""
    _rate_limiter.reset()
