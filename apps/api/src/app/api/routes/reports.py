"""Report endpoints (stubbed)."""

from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.api.dependencies import get_orchestration_service, get_report_repository
from app.schemas.reports import (
    ReportCreateRequest,
    ReportCreateResponse,
    ReportImageUploadResponse,
    ReportProcessingResultRequest,
    ReportStatusResponse,
)
from app.services.interfaces import ReportRepository
from app.services.orchestration import ReportOrchestrationService

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
    orchestration_service: ReportOrchestrationService = Depends(
        get_orchestration_service
    ),
) -> ReportImageUploadResponse:
    """Accept an image upload and enqueue mock async processing."""
    processing_status = await orchestration_service.enqueue_report_image_processing(
        report_id
    )
    return ReportImageUploadResponse(
        report_id=report_id,
        filename=image.filename or "upload.bin",
        content_type=image.content_type,
        status="processing",
        job_id=processing_status.job_id or "missing-job-id",
        uploaded_at=datetime.now(tz=UTC),
        attempt_count=processing_status.attempt_count,
    )


@router.get("/{report_id}/status", response_model=ReportStatusResponse)
async def get_report_status(
    report_id: UUID,
    orchestration_service: ReportOrchestrationService = Depends(
        get_orchestration_service
    ),
) -> ReportStatusResponse:
    """Return processing status for a report."""
    return await orchestration_service.get_report_status(report_id)


@router.post("/{report_id}/processing-result", response_model=ReportStatusResponse)
async def update_processing_result(
    report_id: UUID,
    payload: ReportProcessingResultRequest,
    orchestration_service: ReportOrchestrationService = Depends(
        get_orchestration_service
    ),
) -> ReportStatusResponse:
    """Simulate worker callback and update processing status."""
    if payload.status == "complete":
        return await orchestration_service.mark_processing_complete(report_id)
    return await orchestration_service.mark_processing_failed(
        report_id, error=payload.error or "processing failed"
    )
