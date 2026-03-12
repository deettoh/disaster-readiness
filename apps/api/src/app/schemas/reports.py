"""Report submission schemas."""

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class GeoPoint(BaseModel):
    """Latitude/longitude coordinate pair."""

    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)

    model_config = ConfigDict(
        json_schema_extra={"example": {"latitude": 3.1390, "longitude": 101.6869}}
    )


class ReportCreateRequest(BaseModel):
    """Payload for creating a new hazard report."""

    location: GeoPoint
    note: str | None = Field(default=None, max_length=500)
    user_hazard_label: str | None = None

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "location": {"latitude": 3.1390, "longitude": 101.6869},
                "note": "Water level rising near road shoulder",
                "user_hazard_label": "flooded_road",
            }
        }
    )


class ReportCreateResponse(BaseModel):
    """Response returned after report metadata creation."""

    report_id: UUID
    status: Literal["processing", "complete", "failed"] = "processing"
    created_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "report_id": "9dd8ba26-5eb1-44b2-ab8f-eb47340d67fd",
                "status": "processing",
                "created_at": "2026-02-25T09:45:00Z",
            }
        }
    )


class ReportImageUploadResponse(BaseModel):
    """Response returned after uploading report image metadata."""

    report_id: UUID
    filename: str
    content_type: str | None = None
    status: Literal["processing"] = "processing"
    job_id: str
    uploaded_at: datetime
    attempt_count: int = Field(ge=1)
    file_size_bytes: int = Field(ge=0)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "report_id": "9dd8ba26-5eb1-44b2-ab8f-eb47340d67fd",
                "filename": "hazard.jpg",
                "content_type": "image/jpeg",
                "status": "processing",
                "job_id": "mock-job-9dd8ba26-5eb1-44b2-ab8f-eb47340d67fd",
                "uploaded_at": "2026-02-25T09:45:05Z",
                "attempt_count": 1,
                "file_size_bytes": 482013,
            }
        }
    )


class ReportStatusResponse(BaseModel):
    """Report processing status payload."""

    report_id: UUID
    status: Literal["processing", "complete", "failed"]
    job_id: str | None = None
    error: str | None = None
    attempt_count: int = Field(default=0, ge=0)
    updated_at: datetime

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "report_id": "9dd8ba26-5eb1-44b2-ab8f-eb47340d67fd",
                "status": "processing",
                "job_id": "mock-job-9dd8ba26-5eb1-44b2-ab8f-eb47340d67fd",
                "error": None,
                "attempt_count": 1,
                "updated_at": "2026-02-25T09:45:05Z",
            }
        }
    )


class ReportProcessingResultRequest(BaseModel):
    """Worker callback payload for report processing result."""

    status: Literal["complete", "failed"]
    error: str | None = None

    model_config = ConfigDict(
        json_schema_extra={"example": {"status": "complete", "error": None}}
    )
