"""Shared fixtures for AI tests."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[2]
CLASSIFICATION_SRC = ROOT_DIR / "ai" / "classification" / "src"
for path in (str(ROOT_DIR), str(CLASSIFICATION_SRC)):
    if path not in sys.path:
        sys.path.insert(0, path)


@pytest.fixture
def inference_module():
    """Return hazard classification inference module."""
    return importlib.import_module("hazard_classification.inference")
