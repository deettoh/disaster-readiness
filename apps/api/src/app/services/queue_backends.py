"""Queue backend implementations for orchestration."""

from __future__ import annotations

import asyncio
import logging
from uuid import UUID, uuid4

from app.core.exceptions import ExternalServiceError
from app.services.image_processing import process_report_image_sync
from app.services.interfaces import PostProcessingHooks, ReportStatusStore

logger = logging.getLogger(__name__)


class InProcessQueueClient:
    """In-process queue client that runs jobs inside the API container."""

    def __init__(
        self,
        *,
        status_store: ReportStatusStore,
        post_processing_hooks: PostProcessingHooks,
        database_url: str,
        supabase_url: str | None,
        supabase_key: str | None,
        model_version: str | None = None,
    ) -> None:
        """Initialize in-process queue dependencies."""
        self._status_store = status_store
        self._post_processing_hooks = post_processing_hooks
        self._database_url = database_url
        self._supabase_url = (supabase_url or "").strip()
        self._supabase_key = (supabase_key or "").strip()
        self._model_version = model_version

    async def ping(self) -> bool:
        """Return availability status for in-process queue backend."""
        return True

    async def enqueue_image_processing(
        self,
        report_id: str,
        *,
        image_payload_b64: str | None = None,
        filename: str | None = None,
        content_type: str | None = None,
    ) -> str:
        """Enqueue in-process image processing job."""
        if not image_payload_b64:
            raise ExternalServiceError(
                service="image-processing",
                message="missing image payload for processing job",
                details={"report_id": report_id},
            )
        if not self._supabase_url or not self._supabase_key:
            raise ExternalServiceError(
                service="image-processing",
                message="SUPABASE_URL and SUPABASE_SECRET_KEY must be set",
                details={"report_id": report_id},
            )

        job_id = f"inproc-{uuid4()}"
        asyncio.create_task(
            self._run_job(
                report_id=report_id,
                image_payload_b64=image_payload_b64,
                filename=filename,
                content_type=content_type,
            )
        )
        return job_id

    async def _run_job(
        self,
        *,
        report_id: str,
        image_payload_b64: str,
        filename: str | None,
        content_type: str | None,
    ) -> None:
        """Execute image processing job and update status/hook outputs."""
        report_uuid = UUID(report_id)
        try:
            await asyncio.to_thread(
                process_report_image_sync,
                report_uuid,
                image_payload_b64=image_payload_b64,
                filename=filename,
                content_type=content_type,
                database_url=self._database_url,
                supabase_url=self._supabase_url,
                supabase_key=self._supabase_key,
                model_version=self._model_version,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "in-process image processing failed",
                extra={"report_id": report_id, "error": str(exc)},
            )
            await self._status_store.mark_failed(report_uuid, error=str(exc))
            return

        try:
            await self._status_store.mark_complete(report_uuid)
            await self._post_processing_hooks.trigger_road_penalty_update(report_uuid)
            await self._post_processing_hooks.trigger_readiness_recompute(report_uuid)
            await self._post_processing_hooks.trigger_alert_generation(report_uuid)
        except Exception as exc:  # noqa: BLE001
            logger.exception(
                "post-processing hooks failed",
                extra={"report_id": report_id, "error": str(exc)},
            )
