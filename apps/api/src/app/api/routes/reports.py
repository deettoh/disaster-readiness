"""Report endpoints (stubbed)."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.api.dependencies import get_queue_client, get_report_repository
from app.schemas.reports import (
    ReportCreateRequest,
    ReportCreateResponse,
    ReportImageUploadResponse,
)
from app.services.interfaces import QueueClient, ReportRepository

router = APIRouter(prefix="/reports", tags=["reports"])


@router.post("", response_model=ReportCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_report(
    payload: ReportCreateRequest,
    report_repository: ReportRepository = Depends(get_report_repository),
) -> ReportCreateResponse:
    """Create a report record (stubbed persistence layer)."""
    return await report_repository.create_report(payload)


@router.post(
    "/{report_id}/image",
    response_model=ReportImageUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def upload_report_image(
    report_id: UUID,
    image: UploadFile = File(...),
    queue_client: QueueClient = Depends(get_queue_client),
) -> ReportImageUploadResponse:
    """Accept an image upload and enqueue mock async processing."""
    job_id = await queue_client.enqueue_image_processing(str(report_id))
    return ReportImageUploadResponse(
        report_id=report_id,
        filename=image.filename or "upload.bin",
        content_type=image.content_type,
        status="processing",
        job_id=job_id,
        uploaded_at=datetime.now(tz=UTC),
    )

