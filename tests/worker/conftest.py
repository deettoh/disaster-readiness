"""Shared fixtures for worker tests."""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest

ROOT_DIR = Path(__file__).resolve().parents[2]
WORKER_SRC = ROOT_DIR / "apps" / "worker" / "src"
for path in (str(ROOT_DIR), str(WORKER_SRC)):
    if path not in sys.path:
        sys.path.insert(0, path)

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://postgres:root@localhost:5432/routing_db",
)


@pytest.fixture
def jobs_module():
    """Return worker jobs module for monkeypatching."""
    return importlib.import_module("worker.jobs")


@pytest.fixture
def encoded_image_payload() -> str:
    """Return base64 payload string for a test image byte sequence."""
    import base64

    return base64.b64encode(b"fake-image-content").decode("ascii")
