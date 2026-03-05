"""Worker job integration tests."""

from __future__ import annotations

from pathlib import Path
from uuid import uuid4

import pytest


def test_process_report_image_success_with_mock_redaction(
    jobs_module,
    encoded_image_payload,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Worker should persist mock outputs and mark callback complete."""
    payload: dict[str, object] = {}

    def fake_persist_worker_outputs(**kwargs: object) -> None:
        payload.update(kwargs)

    def fake_notify_processing_result(**kwargs: object) -> None:
        payload["callback"] = kwargs

    report_id = str(uuid4())
    monkeypatch.setattr(jobs_module, "_persist_worker_outputs", fake_persist_worker_outputs)
    monkeypatch.setattr(jobs_module, "_notify_processing_result", fake_notify_processing_result)
    monkeypatch.setattr(
        jobs_module,
        "_classify_image",
        lambda _bytes: jobs_module.ClassificationResult(
            hazard_label="flood",
            confidence=0.91,
            model_version="test-model",
        ),
    )
    monkeypatch.setenv("WORKER_REDACTED_OUTPUT_DIR", str(tmp_path))

    result = jobs_module.process_report_image(
        report_id,
        image_payload_b64=encoded_image_payload,
        filename="hazard.jpg",
        content_type="image/jpeg",
    )
    redacted_path = Path(str(result["redacted_path"]))
    assert redacted_path.exists()
    assert redacted_path.read_bytes() == b"fake-image-content"
    assert result["status"] == "complete"
    assert payload["callback"] is not None


def test_process_report_image_failure_marks_failed(
    jobs_module,
    encoded_image_payload,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    """Worker should trigger failed callback when persistence fails."""
    calls: dict[str, object] = {}

    def fake_persist_worker_outputs(**_kwargs: object) -> None:
        raise RuntimeError("db down")

    def fake_notify_processing_result_safely(**kwargs: object) -> None:
        calls.update(kwargs)

    monkeypatch.setattr(jobs_module, "_persist_worker_outputs", fake_persist_worker_outputs)
    monkeypatch.setattr(
        jobs_module,
        "_notify_processing_result_safely",
        fake_notify_processing_result_safely,
    )
    monkeypatch.setattr(
        jobs_module,
        "_classify_image",
        lambda _bytes: jobs_module.ClassificationResult(
            hazard_label="flood",
            confidence=0.91,
            model_version="test-model",
        ),
    )
    monkeypatch.setenv("WORKER_REDACTED_OUTPUT_DIR", str(tmp_path))

    report_id = str(uuid4())
    with pytest.raises(RuntimeError, match="db down"):
        jobs_module.process_report_image(
            report_id,
            image_payload_b64=encoded_image_payload,
            filename="hazard.jpg",
            content_type="image/jpeg",
        )

    assert str(calls["report_id"]) == report_id
    assert "db down" in str(calls["error_message"])
