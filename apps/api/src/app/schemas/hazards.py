"""Hazard read schemas."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.reports import GeoPoint


class HazardItem(BaseModel):
    """Single hazard item for map/list rendering."""

    report_id: UUID
    hazard_label: str
    confidence: float = Field(ge=0, le=1)
    location: GeoPoint
    redacted_image_url: str | None = None
    observed_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "report_id": "9dd8ba26-5eb1-44b2-ab8f-eb47340d67fd",
                "hazard_label": "flooded_road",
                "confidence": 0.81,
                "location": {"latitude": 3.1390, "longitude": 101.6869},
                "redacted_image_url": "https://example.local/redacted/mock.jpg",
                "observed_at": "2026-02-25T09:46:00Z",
            }
        }
    )


class HazardListResponse(BaseModel):
    """Collection of hazard items."""

    items: list[HazardItem]

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "items": [
                    {
                        "report_id": "9dd8ba26-5eb1-44b2-ab8f-eb47340d67fd",
                        "hazard_label": "flooded_road",
                        "confidence": 0.81,
                        "location": {"latitude": 3.1390, "longitude": 101.6869},
                        "redacted_image_url": "https://example.local/redacted/mock.jpg",
                        "observed_at": "2026-02-25T09:46:00Z",
                    }
                ]
            }
        }
    )
