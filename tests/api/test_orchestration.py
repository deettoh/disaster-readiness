"""Job orchestration tests."""

from uuid import uuid4

import pytest

from app.core.exceptions import ProcessingError
from app.services.mocks import (
    MockPostProcessingHooks,
    MockQueueClient,
    MockReportStatusStore,
)
from app.services.orchestration import ReportOrchestrationService


@pytest.fixture
def orchestration_factory():
    """Build orchestration service with controllable queue behavior."""

    def _build(*, fail_first_attempts: int, max_attempts: int):
        queue_client = MockQueueClient(fail_first_attempts=fail_first_attempts)
        status_store = MockReportStatusStore()
        hooks = MockPostProcessingHooks()
        service = ReportOrchestrationService(
            queue_client=queue_client,
            status_store=status_store,
            post_processing_hooks=hooks,
            enqueue_max_attempts=max_attempts,
            enqueue_backoff_seconds=[0.0] * max_attempts,
        )
        return service, queue_client, hooks

    return _build


@pytest.mark.anyio
async def test_enqueue_retries_and_marks_processing(orchestration_factory) -> None:
    """Orchestration retries enqueue and marks processing state."""
    service, queue_client, _ = orchestration_factory(
        fail_first_attempts=1,
        max_attempts=3,
    )
    report_id = uuid4()
    status = await service.enqueue_report_image_processing(report_id)
    assert status.status == "processing"
    assert status.attempt_count == 2
    assert queue_client.attempts == 2


@pytest.mark.anyio
async def test_enqueue_failure_marks_failed_status(orchestration_factory) -> None:
    """Orchestration sets failed status after retry exhaustion."""
    service, _, _ = orchestration_factory(
        fail_first_attempts=5,
        max_attempts=2,
    )
    report_id = uuid4()
    with pytest.raises(ProcessingError):
        await service.enqueue_report_image_processing(report_id)
    status = await service.get_report_status(report_id)
    assert status.status == "failed"
    assert status.attempt_count == 2
    assert status.error is not None


@pytest.mark.anyio
async def test_complete_status_triggers_all_post_processing_hooks(
    orchestration_factory,
) -> None:
    """Completion marks status complete and triggers downstream hooks."""
    service, _, hooks = orchestration_factory(
        fail_first_attempts=0,
        max_attempts=2,
    )
    report_id = uuid4()
    await service.enqueue_report_image_processing(report_id)
    status = await service.mark_processing_complete(report_id)
    snapshot = hooks.snapshot()
    assert status.status == "complete"
    assert str(report_id) in snapshot["road_penalty_update"]
    assert str(report_id) in snapshot["readiness_recompute"]
    assert str(report_id) in snapshot["alert_generation"]
