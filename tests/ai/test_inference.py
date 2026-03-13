"""Real model inference test on a single sample image."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[2]
SAMPLE_IMAGE_FILE = (
    ROOT_DIR / "data" / "samples" / "classification_inference" / "images" / "sample.jpg"
)
EXPECTED_LABEL = "flood"


def _get_test_image_path() -> Path:
    """Return fixed sample image path for deterministic test coverage."""
    image_path = SAMPLE_IMAGE_FILE
    if not image_path.exists():
        pytest.skip(f"Test image does not exist: {image_path}")
    return image_path


def test_real_model_inference_on_sample_image(inference_module) -> None:
    """Run actual model inference on one configured sample image."""
    image_path = _get_test_image_path()
    valid_labels = set(inference_module.CLASS_LABELS) | {"uncertain"}

    image_bytes = image_path.read_bytes()
    label, confidence = inference_module.predict_hazard(image_bytes)

    assert label in valid_labels
    assert 0.0 <= confidence <= 1.0
    assert label == EXPECTED_LABEL
