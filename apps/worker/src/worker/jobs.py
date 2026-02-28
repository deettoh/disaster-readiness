"""Background job implementations for the worker service."""

import logging
from datetime import UTC, datetime

logger = logging.getLogger(__name__)


def process_report_image(report_id: str) -> dict[str, str]:
    """Mock report-image processing job for integration scaffolding."""
    logger.info("processing report image", extra={"report_id": report_id})
    return {
        "report_id": report_id,
        "status": "complete",
        "processed_at": datetime.now(tz=UTC).isoformat(),
    }
