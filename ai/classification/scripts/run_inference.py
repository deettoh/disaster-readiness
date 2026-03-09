"""Manual runner for hazard classification inference on one image."""

from __future__ import annotations

import os
import sys
from pathlib import Path

from hazard_classification.inference import predict_hazard

ROOT_DIR = Path(__file__).resolve().parents[3]
CLASSIFICATION_SRC = ROOT_DIR / "ai" / "classification" / "src"
DEFAULT_IMAGE_FILE = (
    ROOT_DIR / "data" / "samples" / "classification_inference" / "images" / "sample.jpg"
)
for path in (str(ROOT_DIR), str(CLASSIFICATION_SRC)):
    if path not in sys.path:
        sys.path.insert(0, path)


def _resolve_path(raw_path: str, default_path: Path) -> Path:
    """Resolve env path to absolute path using repo root when needed."""
    if not raw_path.strip():
        return default_path
    path = Path(raw_path).expanduser()
    return path if path.is_absolute() else ROOT_DIR / path


def _get_image_path() -> Path:
    """Read single image path from CLASSIFICATION_TEST_IMAGE_FILE."""
    return _resolve_path(
        os.getenv("CLASSIFICATION_TEST_IMAGE_FILE", ""),
        DEFAULT_IMAGE_FILE,
    )


def main() -> int:
    """Run real model inference on one configured image."""
    image_path = _get_image_path()
    if not image_path.exists():
        print(f"Test image does not exist: {image_path}")
        return 1

    label, confidence = predict_hazard(image_path.read_bytes())
    print(f"{image_path}: label={label}, confidence={confidence:.4f}")


if __name__ == "__main__":
    main()
