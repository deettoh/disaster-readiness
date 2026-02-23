"""Health and liveness endpoints."""

from fastapi import APIRouter

from app.core.config import get_settings
from app.schemas.common import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Liveness endpoint for local/dev/prod probes."""
    settings = get_settings()
    return HealthResponse(
        status="ok",
        service="api",
        version=settings.app_version,
        environment=settings.app_env,
    )

