"""Top-level API router for versioned endpoints."""

from fastapi import APIRouter

from app.api.routes.alerts import router as alerts_router
from app.api.routes.hazards import router as hazards_router
from app.api.routes.readiness import router as readiness_router
from app.api.routes.reports import router as reports_router
from app.schemas.common import ApiInfoResponse

api_router = APIRouter(tags=["api"])
api_router.include_router(reports_router)
api_router.include_router(hazards_router)
api_router.include_router(readiness_router)
api_router.include_router(alerts_router)


@api_router.get("/info", response_model=ApiInfoResponse)
async def api_info() -> ApiInfoResponse:
    """Simple API metadata endpoint for integration smoke checks."""
    return ApiInfoResponse(service="api", message="Backend foundation ready")
