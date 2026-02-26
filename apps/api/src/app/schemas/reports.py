"""Report submission schemas (skeleton)."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field


class GeoPoint(BaseModel):
    """Latitude/longitude coordinate pair."""

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)


class ReportCreateRequest(BaseModel):
    """Payload for creating a new hazard report."""

    location: GeoPoint
    note: str | None = Field(default=None, max_length=500)
    user_hazard_label: str | None = None


class ReportCreateResponse(BaseModel):
    """Response returned after report metadata creation."""

    report_id: UUID
    status: Literal["processing", "complete", "failed"] = "processing"
    created_at: datetime


class ReportImageUploadResponse(BaseModel):
    """Response returned after uploading report image metadata."""

    report_id: UUID
    filename: str
    content_type: str | None = None
    status: Literal["processing"] = "processing"
    job_id: str
    uploaded_at: datetime
    attempt_count: int = Field(ge=1)


class ReportStatusResponse(BaseModel):
    """Report processing status payload."""

    report_id: UUID
    status: Literal["processing", "complete", "failed"]
    job_id: str | None = None
    error: str | None = None
    attempt_count: int = Field(default=0, ge=0)
    updated_at: datetime


class ReportProcessingResultRequest(BaseModel):
    """Worker callback payload for report processing result."""

    status: Literal["complete", "failed"]
    error: str | None = None
