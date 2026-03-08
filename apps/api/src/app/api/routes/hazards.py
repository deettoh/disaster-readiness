"""Hazard endpoints."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_hazard_service
from app.core.privacy import sanitize_redacted_image_url
from app.schemas.hazards import HazardListResponse
from app.services.interfaces import HazardQueryService

router = APIRouter(prefix="/hazards", tags=["hazards"])


@router.get("", response_model=HazardListResponse)
async def list_hazards(
    hazard_service: HazardQueryService = Depends(get_hazard_service),
) -> HazardListResponse:
    """Return hazard list from mock-backed query service."""
    response = await hazard_service.list_hazards()
    sanitized_items = [
        item.model_copy(
            update={
                "redacted_image_url": sanitize_redacted_image_url(item.redacted_image_url)
            }
        )
        for item in response.items
    ]
    return HazardListResponse(items=sanitized_items)
