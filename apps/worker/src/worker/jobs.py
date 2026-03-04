"""Background job implementations for the worker service."""

from __future__ import annotations

import base64
import json
import logging
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib import error, request
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError

try:
    from hazard_classification.inference import predict_hazard as _predict_hazard
except Exception as exc:  # noqa: BLE001
    _predict_hazard = None
    _predict_hazard_import_error = exc
else:
    _predict_hazard_import_error = None

logger = logging.getLogger(__name__)

@dataclass(frozen=True)
class ClassificationResult:
    """Hazard classification output used by worker integration."""

    hazard_label: str
    confidence: float
    model_version: str


def process_report_image(
    report_id: str,
    *,
    image_payload_b64: str | None = None,
    filename: str | None = None,
    content_type: str | None = None,
) -> dict[str, Any]:
    """Process uploaded image, persist AI outputs, and update API status."""
    _ = content_type
    logger.info("processing report image", extra={"report_id": report_id})
    if not image_payload_b64:
        raise ValueError("missing image payload for worker processing")

    report_uuid = UUID(report_id)
    image_bytes = base64.b64decode(image_payload_b64.encode("ascii"))
    image_filename = (filename or "report-image.jpg").strip() or "report-image.jpg"
    output_dir = _redacted_output_dir()
    database_url = os.getenv(
        "WORKER_DATABASE_URL", "postgresql://postgres:root@localhost:5432/routing_db"
    )
    api_base_url = os.getenv("WORKER_API_BASE_URL", "http://localhost:8000/api/v1")

    try:
        classification = _classify_image(image_bytes)
        redacted_image_bytes = _mock_redact(image_bytes)
        redacted_path = _write_redacted_artifact(
            report_id=report_uuid,
            filename=image_filename,
            image_bytes=redacted_image_bytes,
            output_dir=output_dir,
        )
        _persist_worker_outputs(
            report_id=report_uuid,
            redacted_path=redacted_path,
            classification=classification,
            database_url=database_url,
        )
        _notify_processing_result(
            report_id=report_uuid,
            status="complete",
            error_message=None,
            api_base_url=api_base_url,
        )
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "worker image processing failed",
            extra={"report_id": report_id, "error": str(exc)},
        )
        _notify_processing_result_safely(
            report_id=report_uuid,
            error_message=str(exc),
            api_base_url=api_base_url,
        )
        raise

    return {
        "report_id": report_id,
        "status": "complete",
        "hazard_label": classification.hazard_label,
        "confidence": classification.confidence,
        "model_version": classification.model_version,
        "redacted_path": redacted_path,
        "processed_at": datetime.now(tz=UTC).isoformat(),
    }


def _classify_image(image_bytes: bytes) -> ClassificationResult:
    """Run real hazard classification inference and return normalized output."""
    if _predict_hazard is None:
        raise RuntimeError(
            "hazard classification inference import failed at worker startup"
        ) from _predict_hazard_import_error

    hazard_label, confidence = _predict_hazard(image_bytes)
    return ClassificationResult(
        hazard_label=str(hazard_label),
        confidence=float(confidence),
        model_version=os.getenv(
            "WORKER_CLASSIFICATION_MODEL_VERSION",
            "efficientnet-b0-best_model.pth",
        ),
    )


def _mock_redact(image_bytes: bytes) -> bytes:
    """Return passthrough bytes as temporary mocked redaction output."""
    return image_bytes


def _redacted_output_dir() -> Path:
    """Return redacted output directory from env with local default."""
    return Path(
        os.getenv("WORKER_REDACTED_OUTPUT_DIR", "data/processed/redacted")
    ).resolve()


def _safe_filename(filename: str) -> str:
    """Normalize filename to a basename only value."""
    return Path(filename).name or "report-image.jpg"


def _write_redacted_artifact(
    *,
    report_id: UUID,
    filename: str,
    image_bytes: bytes,
    output_dir: Path,
) -> str:
    """Write mocked redacted image artifact and return stored path."""
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%S")
    safe_filename = _safe_filename(filename)
    report_dir = output_dir / str(report_id)
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"redacted-{timestamp}-{safe_filename}"
    path.write_bytes(image_bytes)
    return str(path)


def _engine_from_url(database_url: str) -> Engine:
    """Create SQLAlchemy engine for worker database operations."""
    return create_engine(database_url)


def _persist_worker_outputs(
    *,
    report_id: UUID,
    redacted_path: str,
    classification: ClassificationResult,
    database_url: str,
) -> None:
    """Persist classification prediction and redacted image metadata."""
    prediction_sql = text(
        """
        INSERT INTO public.hazard_predictions (
            geom,
            prediction_type,
            probability,
            model_version,
            valid_from,
            valid_until
        )
        SELECT
            r.geom,
            :prediction_type,
            :probability,
            :model_version,
            now(),
            now() + interval '72 hours'
        FROM public.reports AS r
        WHERE r.id = :report_id
        RETURNING id;
        """
    )
    image_sql = text(
        """
        INSERT INTO public.images (report_id, bucket_path, caption)
        VALUES (:report_id, :bucket_path, :caption)
        RETURNING id;
        """
    )

    engine = _engine_from_url(database_url)
    try:
        with engine.begin() as conn:
            prediction_row = conn.execute(
                prediction_sql,
                {
                    "report_id": report_id,
                    "prediction_type": classification.hazard_label,
                    "probability": classification.confidence,
                    "model_version": classification.model_version,
                },
            ).fetchone()
            if prediction_row is None:
                raise RuntimeError(f"report does not exist: {report_id}")
            conn.execute(
                image_sql,
                {
                    "report_id": report_id,
                    "bucket_path": redacted_path,
                    "caption": "mock-redacted-passthrough",
                },
            )
    except SQLAlchemyError as exc:
        raise RuntimeError("failed to persist worker outputs") from exc
    finally:
        engine.dispose()


def _notify_processing_result(
    *,
    report_id: UUID,
    status: str,
    error_message: str | None,
    api_base_url: str,
) -> None:
    """Notify API processing status callback with retry policy."""
    max_attempts = int(os.getenv("WORKER_CALLBACK_MAX_ATTEMPTS", "3"))
    timeout_seconds = float(os.getenv("WORKER_CALLBACK_TIMEOUT_SECONDS", "8"))
    backoff_seconds = float(os.getenv("WORKER_CALLBACK_BACKOFF_SECONDS", "1.0"))
    callback_url = (
        f"{api_base_url.rstrip('/')}/reports/{report_id}/processing-result"
    )
    body = {"status": status, "error": error_message}
    data = json.dumps(body).encode("utf-8")

    last_error: Exception | None = None
    for attempt in range(1, max_attempts + 1):
        req = request.Request(
            callback_url,
            data=data,
            method="POST",
            headers={"Content-Type": "application/json"},
        )
        try:
            with request.urlopen(req, timeout=timeout_seconds) as response:  # noqa: S310
                if response.status < 200 or response.status >= 300:
                    raise RuntimeError(
                        f"callback returned status {response.status}"
                    )
                return
        except (error.URLError, TimeoutError, RuntimeError) as exc:
            last_error = exc
            if attempt < max_attempts:
                time.sleep(backoff_seconds)

    assert last_error is not None
    raise RuntimeError("failed to notify processing result callback") from last_error


def _notify_processing_result_safely(
    *,
    report_id: UUID,
    error_message: str,
    api_base_url: str,
) -> None:
    """Best effort failed status callback that never raises."""
    try:
        _notify_processing_result(
            report_id=report_id,
            status="failed",
            error_message=error_message,
            api_base_url=api_base_url,
        )
    except Exception:  # noqa: BLE001
        logger.exception(
            "failed to notify worker failure callback",
            extra={"report_id": str(report_id)},
        )
