"""Real model inference test on a single sample image."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_IMAGE_FILE = (
    ROOT_DIR / "data" / "samples" / "classification_inference" / "images" / "sample.jpg"
)


def _load_env_file() -> None:
    """Load key/value pairs from repo root .env into process env."""
    env_path = ROOT_DIR / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        if not key:
            continue
        value = value.strip().strip('"').strip("'")
        os.environ.setdefault(key, value)


def _resolve_path(raw_path: str, default_path: Path) -> Path:
    """Resolve env path to absolute path using repo root when needed."""
    if not raw_path.strip():
        return default_path
    path = Path(raw_path).expanduser()
    return path if path.is_absolute() else ROOT_DIR / path


def _get_test_image_path() -> Path:
    """Read single image path from CLASSIFICATION_TEST_IMAGE_FILE."""
    _load_env_file()
    image_path = _resolve_path(
        os.getenv("CLASSIFICATION_TEST_IMAGE_FILE", ""),
        DEFAULT_IMAGE_FILE,
    )
    if not image_path.exists():
        pytest.skip(f"Test image does not exist: {image_path}")
    return image_path


def _get_expected_label() -> str:
    """Read expected label from CLASSIFICATION_EXPECTED_LABEL."""
    _load_env_file()
    expected_label = os.getenv("CLASSIFICATION_EXPECTED_LABEL", "").strip()
    if not expected_label:
        pytest.skip("Set CLASSIFICATION_EXPECTED_LABEL to run inference label assertion.")
    return expected_label


def test_real_model_inference_on_sample_image(inference_module) -> None:
    """Run actual model inference on one configured sample image."""
    image_path = _get_test_image_path()
    expected_label = _get_expected_label()
    valid_labels = set(inference_module.CLASS_LABELS) | {"uncertain"}

    image_bytes = image_path.read_bytes()
    label, confidence = inference_module.predict_hazard(image_bytes)

    assert label in valid_labels
    assert 0.0 <= confidence <= 1.0
    assert label == expected_label
