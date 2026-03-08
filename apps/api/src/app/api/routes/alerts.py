"""Alert endpoints."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_alert_service
from app.schemas.alerts import AlertListResponse
from app.services.interfaces import AlertQueryService

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=AlertListResponse)
async def list_alerts(
    alert_service: AlertQueryService = Depends(get_alert_service),
) -> AlertListResponse:
    """Return alerts from mock-backed query service."""
    return await alert_service.list_alerts()

