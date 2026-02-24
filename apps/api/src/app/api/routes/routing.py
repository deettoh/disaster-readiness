"""Routing endpoints (stubbed)."""

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_routing_service
from app.core.exceptions import DomainValidationError
from app.schemas.reports import GeoPoint
from app.schemas.routing import RouteRequest, RouteResponse
from app.services.interfaces import RoutingService

router = APIRouter(prefix="/route", tags=["routing"])


@router.get("", response_model=RouteResponse)
async def get_route(
    origin_lat: float = Query(..., ge=-90, le=90),
    origin_lng: float = Query(..., ge=-180, le=180),
    destination_lat: float | None = Query(default=None, ge=-90, le=90),
    destination_lng: float | None = Query(default=None, ge=-180, le=180),
    shelter_id: str | None = Query(default=None),
    routing_service: RoutingService = Depends(get_routing_service),
) -> RouteResponse:
    """Return an evacuation route from mock-backed routing service."""
    if (destination_lat is None) != (destination_lng is None):
        raise DomainValidationError(
            message="destination_lat and destination_lng must be provided together",
            field="destination_lat,destination_lng",
        )

    origin = GeoPoint(latitude=origin_lat, longitude=origin_lng)
    destination = (
        GeoPoint(latitude=destination_lat, longitude=destination_lng)
        if destination_lat is not None and destination_lng is not None
        else None
    )
    payload = RouteRequest(origin=origin, destination=destination, shelter_id=shelter_id)
    return await routing_service.compute_route(payload)
