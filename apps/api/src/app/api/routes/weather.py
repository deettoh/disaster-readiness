"""Weather endpoints."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_weather_service
from app.schemas.weather import WeatherSnapshotResponse
from app.services.interfaces import WeatherQueryService

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("", response_model=WeatherSnapshotResponse)
async def get_weather_snapshot(
    weather_service: WeatherQueryService = Depends(get_weather_service),
) -> WeatherSnapshotResponse:
    """Return current rainfall readings for all PJ neighbourhoods."""
    return await weather_service.get_weather_snapshot()
