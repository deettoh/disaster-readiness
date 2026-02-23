"""Routing schemas (skeleton)."""

from pydantic import BaseModel, Field

from app.schemas.reports import GeoPoint


class RouteRequest(BaseModel):
    """Route computation input payload."""

    origin: GeoPoint
    destination: GeoPoint | None = None
    shelter_id: str | None = None


class RouteResponse(BaseModel):
    """Route computation output payload."""

    route_geojson: dict
    distance_meters: float = Field(ge=0)
    eta_minutes: float = Field(ge=0)
