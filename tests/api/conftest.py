"""Shared fixtures for API tests."""

from __future__ import annotations

import importlib
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

ROOT_DIR = Path(__file__).resolve().parents[2]
API_SRC = ROOT_DIR / "apps" / "api" / "src"
for path in (str(ROOT_DIR), str(API_SRC)):
    if path not in sys.path:
        sys.path.insert(0, path)

os.environ.setdefault(
    "DATABASE_URL",
    "postgresql://postgres:root@localhost:5432/routing_db",
)

app_module = importlib.import_module("app.main")
dependencies_module = importlib.import_module("app.api.dependencies")
config_module = importlib.import_module("app.core.config")
schemas_hazards_module = importlib.import_module("app.schemas.hazards")
schemas_reports_module = importlib.import_module("app.schemas.reports")


@pytest.fixture
def app():
    """Return FastAPI app instance."""
    return app_module.app


@pytest.fixture
def client(app):
    """Provide a test client for API tests."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def dependencies():
    """Expose dependency module for targeted test assertions."""
    return dependencies_module


@pytest.fixture
def config():
    """Expose config module for settings overrides."""
    return config_module


@pytest.fixture
def Settings(config):
    """Expose Settings class for test specific overrides."""
    return config.Settings


@pytest.fixture
def report_id_str() -> str:
    """Return a random report ID as string."""
    return str(uuid4())


@pytest.fixture
def report_create_payload() -> dict[str, object]:
    """Return a standard report create payload."""
    return {
        "location": {"latitude": 3.1390, "longitude": 101.6869},
        "note": "Water level rising",
        "user_hazard_label": "flooded_road",
    }


@pytest.fixture
def valid_image_upload() -> tuple[str, bytes, str]:
    """Return a standard valid image upload tuple."""
    return ("hazard.jpg", b"stub-image-bytes", "image/jpeg")


@pytest.fixture(autouse=True)
def cleanup_dependency_state(app, dependencies):
    """Reset dependency override and rate-limiter state after each test."""
    yield
    app.dependency_overrides.clear()
    dependencies.reset_rate_limiter_state()


@pytest.fixture
def custom_settings(app, config):
    """Provide helper to override settings dependency for a test."""
    get_settings_func = config.get_settings

    def _set_settings(**kwargs) -> None:
        custom = config.Settings(**kwargs)
        app.dependency_overrides[get_settings_func] = lambda: custom

    return _set_settings


@pytest.fixture
def unsafe_hazard_service(dependencies):
    """Provide fake hazard service with unsafe URLs for sanitization tests."""
    original_service = dependencies._hazard_service

    class UnsafeHazardService:
        async def list_hazards(self) -> schemas_hazards_module.HazardListResponse:
            return schemas_hazards_module.HazardListResponse(
                items=[
                    schemas_hazards_module.HazardItem(
                        report_id=uuid4(),
                        hazard_label="flooded_road",
                        confidence=0.72,
                        location=schemas_reports_module.GeoPoint(
                            latitude=3.1390,
                            longitude=101.6869,
                        ),
                        redacted_image_url="https://example.local/uploads/original.jpg",
                        observed_at=datetime.now(tz=UTC),
                    ),
                    schemas_hazards_module.HazardItem(
                        report_id=uuid4(),
                        hazard_label="debris",
                        confidence=0.84,
                        location=schemas_reports_module.GeoPoint(
                            latitude=3.1400,
                            longitude=101.6875,
                        ),
                        redacted_image_url="https://example.local/redacted/safe.jpg",
                        observed_at=datetime.now(tz=UTC),
                    ),
                ]
            )

    service = UnsafeHazardService()
    dependencies._hazard_service = service
    yield service
    dependencies._hazard_service = original_service


@pytest.fixture
def override_hazard_service(app, dependencies):
    """Override hazard service dependency with a custom implementation."""
    get_hazard_service = dependencies.get_hazard_service

    def _override(service) -> None:
        app.dependency_overrides[get_hazard_service] = lambda: service

    return _override
