"""Report endpoints."""

import base64
from datetime import UTC, datetime
from uuid import UUID

from fastapi import APIRouter, Depends, File, UploadFile, status

from app.api.dependencies import (
    enforce_report_create_rate_limit,
    enforce_report_image_rate_limit,
    get_orchestration_service,
    get_report_repository,
)
from app.core.config import Settings, get_settings
from app.core.upload_validation import (
    validate_report_image_content_type,
    validate_report_image_filename,
    validate_report_image_size,
)
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


@router.post(
    "",
    response_model=ReportCreateResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(enforce_report_create_rate_limit)],
    summary="Create report metadata",
    description="Create report metadata before image upload processing.",
)
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
    dependencies=[Depends(enforce_report_image_rate_limit)],
    summary="Upload report image",
    description=(
        "Accept multipart image upload, validate file constraints, and enqueue "
        "background processing."
    ),
)
async def upload_report_image(
    report_id: UUID,
    image: UploadFile = File(...),
    settings: Settings = Depends(get_settings),
    orchestration_service: ReportOrchestrationService = Depends(
        get_orchestration_service
    ),
) -> ReportImageUploadResponse:
    """Accept an image upload and enqueue mock async processing."""
    normalized_content_type = validate_report_image_content_type(
        content_type=image.content_type,
        allowed_content_types=settings.upload_allowed_content_types,
    )
    normalized_filename = validate_report_image_filename(
        filename=image.filename,
        normalized_content_type=normalized_content_type,
    )
    file_size_bytes = validate_report_image_size(
        upload_file=image,
        max_size_bytes=settings.upload_max_size_bytes,
    )
    image.file.seek(0)
    image_payload_b64 = base64.b64encode(image.file.read()).decode("ascii")
    processing_status = await orchestration_service.enqueue_report_image_processing(
        report_id,
        image_payload_b64=image_payload_b64,
        filename=normalized_filename,
        content_type=normalized_content_type,
    )
    return ReportImageUploadResponse(
        report_id=report_id,
        filename=normalized_filename,
        content_type=normalized_content_type,
        status="processing",
        job_id=processing_status.job_id or "missing-job-id",
        uploaded_at=datetime.now(tz=UTC),
        attempt_count=processing_status.attempt_count,
        file_size_bytes=file_size_bytes,
    )


@router.get(
    "/{report_id}/status",
    response_model=ReportStatusResponse,
    summary="Get report processing status",
)
async def get_report_status(
    report_id: UUID,
    orchestration_service: ReportOrchestrationService = Depends(
        get_orchestration_service
    ),
) -> ReportStatusResponse:
    """Return processing status for a report."""
    return await orchestration_service.get_report_status(report_id)


@router.post(
    "/{report_id}/processing-result",
    response_model=ReportStatusResponse,
    summary="Update report processing result",
    description="Worker callback stub endpoint for completion/failure updates.",
)
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
