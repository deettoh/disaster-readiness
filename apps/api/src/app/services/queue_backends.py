"""Queue backend implementations for orchestration."""

from app.core.exceptions import ExternalServiceError


class RQQueueClient:
    """Redis + RQ queue client implementation."""

    def __init__(
        self,
        *,
        redis_url: str,
        queue_name: str,
        default_timeout: int,
        retry_max: int,
        retry_intervals: list[int],
    ) -> None:
        """Initialize RQ queue client and Redis connection."""
        try:
            from redis import Redis
            from rq import Queue, Retry
        except ImportError as exc:
            raise ExternalServiceError(
                service="rq",
                message="redis/rq dependencies are not installed",
            ) from exc

        self._redis = Redis.from_url(redis_url)
        self._queue = Queue(
            name=queue_name,
            connection=self._redis,
            default_timeout=default_timeout,
        )
        self._retry = Retry(max=retry_max, interval=retry_intervals)

    async def ping(self) -> bool:
        """Check Redis connectivity for queue backend."""
        try:
            return bool(self._redis.ping())
        except Exception:
            return False

    async def enqueue_image_processing(
        self,
        report_id: str,
        *,
        image_payload_b64: str | None = None,
        filename: str | None = None,
        content_type: str | None = None,
    ) -> str:
        """Enqueue report image processing job in RQ."""
        if not image_payload_b64:
            raise ExternalServiceError(
                service="rq",
                message="missing image payload for worker job",
                details={"report_id": report_id},
            )
        try:
            job = self._queue.enqueue(
                "worker.jobs.process_report_image",
                kwargs={
                    "report_id": report_id,
                    "image_payload_b64": image_payload_b64,
                    "filename": filename,
                    "content_type": content_type,
                },
                retry=self._retry,
            )
        except Exception as exc:
            raise ExternalServiceError(
                service="rq",
                message="failed to enqueue report image processing job",
                details={"report_id": report_id, "error": str(exc)},
            ) from exc
        return str(job.id)
