"""Routing schemas."""

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.reports import GeoPoint


class RouteRequest(BaseModel):
    """Route computation input payload."""

    origin: GeoPoint
    destination: GeoPoint | None = None
    shelter_id: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "origin": {"latitude": 3.1390, "longitude": 101.6869},
                "destination": {"latitude": 3.1410, "longitude": 101.6890},
                "shelter_id": None,
            }
        }
    )


class RouteResponse(BaseModel):
    """Route computation output payload."""

    route_geojson: dict
    distance_meters: float = Field(ge=0)
    eta_minutes: float = Field(ge=0)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "route_geojson": {
                    "type": "FeatureCollection",
                    "features": [
                        {
                            "type": "Feature",
                            "geometry": {
                                "type": "LineString",
                                "coordinates": [[101.6869, 3.1390], [101.6890, 3.1410]],
                            },
                            "properties": {"mode": "evacuation"},
                        }
                    ],
                },
                "distance_meters": 500.0,
                "eta_minutes": 7.5,
            }
        }
    )
