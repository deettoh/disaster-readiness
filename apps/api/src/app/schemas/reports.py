"""Report submission schemas (skeleton)."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class GeoPoint(BaseModel):
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class ReportCreateRequest(BaseModel):
    location: GeoPoint
    note: str | None = Field(default=None, max_length=500)
    user_hazard_label: str | None = None


class ReportCreateResponse(BaseModel):
    report_id: UUID
    status: Literal["processing", "complete", "failed"] = "processing"
    created_at: datetime
