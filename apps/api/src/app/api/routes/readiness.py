"""Readiness endpoints (stubbed)."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_readiness_service
from app.schemas.readiness import ReadinessListResponse
from app.services.interfaces import ReadinessQueryService

router = APIRouter(prefix="/readiness", tags=["readiness"])


@router.get("", response_model=ReadinessListResponse)
async def list_readiness(
    readiness_service: ReadinessQueryService = Depends(get_readiness_service),
) -> ReadinessListResponse:
    """Return readiness scores from mock-backed query service."""
    return await readiness_service.list_readiness()

