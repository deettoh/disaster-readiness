"""Background job implementations for the worker service."""

import logging
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
    """Hazard-classification output used by worker integration."""

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
    try:
        classification = _classify_image(image_bytes)
    except Exception as exc:  # noqa: BLE001
        logger.exception(
            "worker image processing failed",
            extra={"report_id": report_id, "error": str(exc)},
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
    max_attempts = int(os.getenv("WORKER_CALLBACK_MAX_ATTEMPTS", "3"))
    timeout_seconds = float(os.getenv("WORKER_CALLBACK_TIMEOUT_SECONDS", "8"))
    )
