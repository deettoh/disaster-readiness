"""Top-level API router for versioned endpoints."""

from fastapi import APIRouter

from app.schemas.common import ApiInfoResponse

api_router = APIRouter(tags=["api"])


@api_router.get("/info", response_model=ApiInfoResponse)
async def api_info() -> ApiInfoResponse:
    """Simple API metadata endpoint for integration smoke checks."""
    return ApiInfoResponse(service="api", message="Backend foundation ready")

