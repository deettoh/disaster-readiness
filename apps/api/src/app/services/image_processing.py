"""Image processing pipeline for hazard report uploads."""

from __future__ import annotations

import base64
import logging
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib import request
from uuid import UUID

from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.engine.url import make_url
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.pool import NullPool

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ClassificationResult:
    """Hazard classification output for persistence."""

    hazard_label: str
    confidence: float
    model_version: str


def process_report_image_sync(
    report_id: UUID,
    *,
    image_payload_b64: str | None,
    filename: str | None,
    content_type: str | None,
    database_url: str,
    supabase_url: str,
    supabase_key: str,
    model_version: str | None = None,
) -> dict[str, Any]:
    """Process uploaded image, persist AI outputs, and return metadata."""
    _ = content_type
    if not image_payload_b64:
        raise ValueError("missing image payload for processing")

    logger.info("processing report image", extra={"report_id": str(report_id)})
    image_bytes = base64.b64decode(image_payload_b64.encode("ascii"))
    image_filename = (filename or "report-image.jpg").strip() or "report-image.jpg"
    if not database_url:
        raise RuntimeError("DATABASE_URL must be set for processing persistence")
    supabase_url = supabase_url.strip()
    supabase_key = supabase_key.strip()
    if not supabase_url or not supabase_key:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SECRET_KEY must be set")

    classification = _classify_image(image_bytes, model_version=model_version)
    redacted_image_bytes = _redact_image(image_bytes)
    redacted_path = _upload_redacted_image(
        report_id=report_id,
        filename=image_filename,
        image_bytes=redacted_image_bytes,
        supabase_url=supabase_url,
        supabase_key=supabase_key,
    )
    _persist_processing_outputs(
        report_id=report_id,
        redacted_path=redacted_path,
        classification=classification,
        database_url=database_url,
    )

    return {
        "report_id": str(report_id),
        "status": "complete",
        "hazard_label": classification.hazard_label,
        "confidence": classification.confidence,
        "model_version": classification.model_version,
        "redacted_path": redacted_path,
        "processed_at": datetime.now(tz=UTC).isoformat(),
    }


def _classify_image(
    image_bytes: bytes,
    *,
    model_version: str | None,
) -> ClassificationResult:
    """Run hazard classification inference and normalize output."""
    # Local import keeps mock only environments usable without heavy deps.
    try:
        from hazard_classification.inference import predict_hazard
    except Exception as exc:
        raise RuntimeError(
            "hazard classification inference import failed during processing"
        ) from exc

    hazard_label, confidence = predict_hazard(image_bytes)
    resolved_version = (
        model_version
        or os.getenv("IMAGE_PROCESSING_MODEL_VERSION")
        or os.getenv("WORKER_CLASSIFICATION_MODEL_VERSION")
        or "efficientnet-b0-best_model.pth"
    )
    return ClassificationResult(
        hazard_label=str(hazard_label),
        confidence=float(confidence),
        model_version=resolved_version,
    )


def _redact_image(image_bytes: bytes) -> bytes:
    """Run privacy redaction pipeline over the image bytes."""
    # Local import keeps mock only environments usable without heavy deps.
    try:
        from privacy_redaction import RedactionPipeline
    except Exception as exc:
        raise RuntimeError(
            "privacy redaction inference import failed during processing"
        ) from exc

    import cv2
    import numpy as np

    nparr = np.frombuffer(image_bytes, np.uint8)
    img_np = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

    if img_np is None:
        raise ValueError("could not decode image bytes into CV2 array")

    redactor = RedactionPipeline()
    redacted_np = redactor.redact(img_np)

    success, encoded_image = cv2.imencode(".jpg", redacted_np)
    if not success:
        raise ValueError("failed to encode redacted image to JPEG")

    return encoded_image.tobytes()


def _safe_filename(filename: str) -> str:
    """Normalize filename to a basename only value."""
    return Path(filename).name or "report-image.jpg"


def _upload_redacted_image(
    *,
    report_id: UUID,
    filename: str,
    image_bytes: bytes,
    supabase_url: str,
    supabase_key: str,
) -> str:
    """Upload redacted image to Supabase and return the public URL."""
    timestamp = datetime.now(tz=UTC).strftime("%Y%m%dT%H%M%S")
    safe_filename = _safe_filename(filename)
    bucket_path = f"{report_id}/redacted-{timestamp}-{safe_filename}"

    base_url = supabase_url.rstrip("/")
    upload_url = f"{base_url}/storage/v1/object/images/{bucket_path}"
    req = request.Request(upload_url, data=image_bytes, method="POST")
    req.add_header("Authorization", f"Bearer {supabase_key}")
    req.add_header("apikey", supabase_key)
    req.add_header("Content-Type", "image/jpeg")

    with request.urlopen(req, timeout=10) as response:  # noqa: S310
        if response.status >= 300:
            raise RuntimeError(f"failed to upload image: {response.status}")

    return f"{base_url}/storage/v1/object/public/images/{bucket_path}"


def _engine_from_url(database_url: str) -> Engine:
    """Create SQLAlchemy engine for processing DB operations using NullPool."""
    url = make_url(database_url)
    connect_args: dict[str, Any] = {}
    if url.drivername.startswith("postgres"):
        url = url.set(drivername="postgresql+psycopg2")
        sslmode = (url.query.get("sslmode") or "").lower()
        if sslmode in {"require", "verify-ca", "verify-full"}:
            import ssl

            connect_args["ssl_context"] = ssl.create_default_context()
            query = dict(url.query)
            query.pop("sslmode", None)
            url = url.set(query=query)
    return create_engine(url, poolclass=NullPool, connect_args=connect_args)


def _persist_processing_outputs(
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
    report_sql = text(
        """
        UPDATE public.reports
        SET hazard_type = :prediction_type,
            confidence = :probability
        WHERE id = :report_id;
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
                    "caption": "redacted-upload",
                },
            )
            conn.execute(
                report_sql,
                {
                    "report_id": report_id,
                    "prediction_type": classification.hazard_label,
                    "probability": classification.confidence,
                },
            )
    except SQLAlchemyError as exc:
        raise RuntimeError("failed to persist processing outputs") from exc
    finally:
        engine.dispose()
