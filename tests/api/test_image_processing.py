"""Image processing pipeline tests."""

from __future__ import annotations

import base64
from uuid import UUID, uuid4

import pytest

from app.services import image_processing as image_processing_module


@pytest.fixture
def encoded_image_payload() -> str:
    """Return base64 payload string for a test image byte sequence."""
    return base64.b64encode(b"fake-image-content").decode("ascii")


def test_process_report_image_sync_success(
    encoded_image_payload: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Processing should persist outputs and return metadata."""
    payload: dict[str, object] = {}

    def fake_persist_processing_outputs(**kwargs: object) -> None:
        payload.update(kwargs)

    monkeypatch.setattr(
        image_processing_module,
        "_persist_processing_outputs",
        fake_persist_processing_outputs,
    )
    monkeypatch.setattr(
        image_processing_module,
        "_upload_redacted_image",
        lambda **_kwargs: "https://example.local/redacted.jpg",
    )
    monkeypatch.setattr(
        image_processing_module,
        "_classify_image",
        lambda *_args, **_kwargs: image_processing_module.ClassificationResult(
            hazard_label="flood",
            confidence=0.91,
            model_version="test-model",
        ),
    )
    monkeypatch.setattr(
        image_processing_module, "_redact_image", lambda _bytes: b"redacted"
    )

    report_id = UUID("6e3b76b2-5bb9-4e72-8d63-861e6f05e0b5")
    result = image_processing_module.process_report_image_sync(
        report_id,
        image_payload_b64=encoded_image_payload,
        filename="hazard.jpg",
        content_type="image/jpeg",
        database_url="postgresql://postgres:root@localhost:5432/routing_db",
        supabase_url="https://example.supabase.co",
        supabase_key="fake-key",
        model_version="test-model",
    )

    assert result["status"] == "complete"
    assert result["hazard_label"] == "flood"
    assert payload["report_id"] == report_id


def test_process_report_image_sync_raises_on_persist_failure(
    encoded_image_payload: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Processing should raise when persistence fails."""

    def fake_persist_processing_outputs(**_kwargs: object) -> None:
        raise RuntimeError("db down")

    monkeypatch.setattr(
        image_processing_module,
        "_persist_processing_outputs",
        fake_persist_processing_outputs,
    )
    monkeypatch.setattr(
        image_processing_module,
        "_upload_redacted_image",
        lambda **_kwargs: "https://example.local/redacted.jpg",
    )
    monkeypatch.setattr(
        image_processing_module,
        "_classify_image",
        lambda *_args, **_kwargs: image_processing_module.ClassificationResult(
            hazard_label="flood",
            confidence=0.91,
            model_version="test-model",
        ),
    )
    monkeypatch.setattr(
        image_processing_module, "_redact_image", lambda _bytes: b"redacted"
    )

    with pytest.raises(RuntimeError, match="db down"):
        image_processing_module.process_report_image_sync(
            uuid4(),
            image_payload_b64=encoded_image_payload,
            filename="hazard.jpg",
            content_type="image/jpeg",
            database_url="postgresql://postgres:root@localhost:5432/routing_db",
            supabase_url="https://example.supabase.co",
            supabase_key="fake-key",
            model_version="test-model",
        )
