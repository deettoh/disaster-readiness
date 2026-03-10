"""Integration test for face + plate redaction.

Usage:
    poetry run python ai/redaction/scripts/run_redaction.py
"""

import logging
import sys
from pathlib import Path

import cv2
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parents[3]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

from ai.redaction.src.privacy_redaction.blur import blur_boxes  # noqa: E402
from ai.redaction.src.privacy_redaction.face_detector import FaceDetector  # noqa: E402
from ai.redaction.src.privacy_redaction.plate_detector import (
    PlateDetector,  # noqa: E402
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Run face and plate redaction on a sample image."""
    image_path = PROJECT_ROOT / "data/samples/redaction_inference/sample.jpg"

    output_dir = PROJECT_ROOT / "ai/redaction/artifacts"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "redacted_output.jpg"

    if not image_path.exists():
        logger.error(f"Sample image not found at {image_path}")
        return

    logger.info(f"Loading image from {image_path}")
    image = cv2.imread(str(image_path))
    if image is None:
        logger.error(f"Could not read image at {image_path}")
        return

    logger.info("Initializing detectors...")
    face_detector = FaceDetector()
    plate_detector = PlateDetector()

    logger.info("Running face detection...")
    face_boxes = face_detector.detect_faces(image)
    logger.info(f"Detected {len(face_boxes)} face boxes.")

    logger.info("Running plate detection...")
    plate_boxes = plate_detector.detect(image)
    logger.info(f"Detected {len(plate_boxes)} plate boxes.")

    all_boxes = face_boxes + plate_boxes

    if all_boxes:
        logger.info(f"Applying redaction to {len(all_boxes)} regions...")
        redacted = blur_boxes(image.copy(), all_boxes)

        cv2.imwrite(str(output_path), redacted)
        logger.info(f"Redacted image saved to: {output_path}")
    else:
        logger.info("No regions detected for redaction.")


if __name__ == "__main__":
    main()
