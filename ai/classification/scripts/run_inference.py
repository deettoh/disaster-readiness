"""Manual runner for hazard classification inference on one image.

Usage:
    poetry run python ai/classification/scripts/run_inference.py
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[3]
CLASSIFICATION_SRC = ROOT_DIR / "ai" / "classification" / "src"
DEFAULT_IMAGE_FILE = (
    ROOT_DIR / "data" / "samples" / "classification_inference" / "images" / "sample.jpg"
)
for path in (str(ROOT_DIR), str(CLASSIFICATION_SRC)):
    if path not in sys.path:
        sys.path.insert(0, path)

from hazard_classification.inference import predict_hazard  # noqa: E402


def main() -> int:
    """Run real model inference on one configured image."""
    image_path = DEFAULT_IMAGE_FILE
    if not image_path.exists():
        print(f"Test image does not exist: {image_path}")
        return 1

    label, confidence = predict_hazard(image_path.read_bytes())
    print(f"{image_path}: label={label}, confidence={confidence:.4f}")


if __name__ == "__main__":
    main()
