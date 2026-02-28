"""Orchestration service for report image processing jobs."""

import asyncio
from uuid import UUID

from app.core.exceptions import ProcessingError
from app.schemas.reports import ReportStatusResponse
from app.services.interfaces import PostProcessingHooks, QueueClient, ReportStatusStore


class ReportOrchestrationService:
    """Coordinates queueing, status updates, retries, and downstream triggers."""

    def __init__(
        self,
        *,
        queue_client: QueueClient,
        status_store: ReportStatusStore,
        post_processing_hooks: PostProcessingHooks,
        enqueue_max_attempts: int,
        enqueue_backoff_seconds: list[float],
    ) -> None:
        """Initialize orchestration dependencies and retry policy."""
        self._queue_client = queue_client
        self._status_store = status_store
        self._post_processing_hooks = post_processing_hooks
        self._enqueue_max_attempts = enqueue_max_attempts
        self._enqueue_backoff_seconds = enqueue_backoff_seconds

    async def check_queue_connectivity(self) -> bool:
        """Return queue backend availability."""
        return await self._queue_client.ping()

    async def enqueue_report_image_processing(self, report_id: UUID) -> ReportStatusResponse:
        """Enqueue image processing with retry and status tracking."""
        last_error: str | None = None
        for attempt in range(1, self._enqueue_max_attempts + 1):
            try:
                job_id = await self._queue_client.enqueue_image_processing(str(report_id))
                return await self._status_store.mark_processing(
                    report_id,
                    job_id=job_id,
                    attempt_count=attempt,
                )
            except Exception as exc:  # noqa: BLE001
                last_error = str(exc)
                if attempt < self._enqueue_max_attempts:
                    delay_seconds = self._retry_delay_for_attempt(attempt)
                    if delay_seconds > 0:
                        await asyncio.sleep(delay_seconds)

        assert last_error is not None
        await self._status_store.mark_failed(
            report_id,
            error=last_error,
            attempt_count=self._enqueue_max_attempts,
        )
        raise ProcessingError(
            message="failed to enqueue image processing job after retries",
            details={"report_id": str(report_id), "error": last_error},
        )

    async def mark_processing_complete(self, report_id: UUID) -> ReportStatusResponse:
        """Mark report complete and trigger downstream post-processing hooks."""
        status = await self._status_store.mark_complete(report_id)
        await self._post_processing_hooks.trigger_road_penalty_update(report_id)
        await self._post_processing_hooks.trigger_readiness_recompute(report_id)
        await self._post_processing_hooks.trigger_alert_generation(report_id)
        return status

    async def mark_processing_failed(
        self, report_id: UUID, *, error: str
    ) -> ReportStatusResponse:
        """Mark report processing as failed."""
        return await self._status_store.mark_failed(report_id, error=error)

    async def get_report_status(self, report_id: UUID) -> ReportStatusResponse:
        """Return current processing status for report."""
        return await self._status_store.get_status(report_id)

    def _retry_delay_for_attempt(self, attempt: int) -> float:
        """Return configured retry delay for a given attempt index."""
        if not self._enqueue_backoff_seconds:
            return 0.0
        idx = min(attempt - 1, len(self._enqueue_backoff_seconds) - 1)
        return self._enqueue_backoff_seconds[idx]
