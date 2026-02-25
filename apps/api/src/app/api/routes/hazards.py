"""Hazard endpoints (stubbed)."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_hazard_service
from app.schemas.hazards import HazardListResponse
from app.services.interfaces import HazardQueryService

router = APIRouter(prefix="/hazards", tags=["hazards"])


@router.get("", response_model=HazardListResponse)
async def list_hazards(
    hazard_service: HazardQueryService = Depends(get_hazard_service),
) -> HazardListResponse:
    """Return hazard list from mock-backed query service."""
    return await hazard_service.list_hazards()

