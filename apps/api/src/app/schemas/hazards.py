"""Hazard read schemas (skeleton)."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.schemas.reports import GeoPoint


class HazardItem(BaseModel):
    report_id: UUID
    hazard_label: str
    confidence: float = Field(ge=0, le=1)
    location: GeoPoint
    redacted_image_url: str | None = None
    observed_at: datetime


class HazardListResponse(BaseModel):
    items: list[HazardItem]
