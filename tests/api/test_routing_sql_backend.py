"""SQL routing backend integration tests for contract wiring."""

from __future__ import annotations

from typing import Any, cast

import pytest

from app.core.config import Settings
from app.core.exceptions import DomainValidationError, NotFoundError, ProcessingError
from app.schemas.reports import GeoPoint
from app.schemas.routing import RouteRequest
from app.services.routing_sql import SQLRoutingService


class _FakeResult:
    """Return a preset database row for fetchone()."""

    def __init__(self, row: tuple[Any, ...] | None) -> None:
        """Initialize with a row payload."""
        self._row = row

    def fetchone(self) -> tuple[Any, ...] | None:
        """Return the configured row once per execute call."""
        return self._row


class _FakeConnection:
    """Minimal SQLAlchemy-like connection context manager for testing."""

    def __init__(self, rows: list[tuple[Any, ...] | None]) -> None:
        """Initialize a deterministic row stream."""
        self._rows = rows
        self._idx = 0

    def __enter__(self) -> _FakeConnection:
        """Enter context manager."""
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> bool:
        """Exit context manager without suppressing exceptions."""
        return False

    def execute(self, _statement: Any, _params: dict[str, Any]) -> _FakeResult:
        """Return the next configured result row."""
        row = self._rows[self._idx] if self._idx < len(self._rows) else None
        self._idx += 1
        return _FakeResult(row)


class _FakeEngine:
    """Minimal SQLAlchemy-like engine for deterministic unit tests."""

    def __init__(self, rows: list[tuple[Any, ...] | None]) -> None:
        """Initialize with execute() rows for one query transaction."""
        self._rows = rows

    def connect(self) -> _FakeConnection:
        """Return a fake connection yielding configured rows."""
        return _FakeConnection(rows=self._rows)


@pytest.mark.anyio
async def test_sql_routing_service_maps_contract_output() -> None:
    """Service should map contract SQL output to RouteResponse schema."""
    fake_engine = _FakeEngine(
        rows=[
            (1001,),
            (2002,),
            (
                5420.0,
                750.0,
                '{"type":"LineString","coordinates":[[101.6869,3.139],[101.689,3.141]]}',
            ),
        ]
    )
    service = SQLRoutingService(
        database_url="postgresql://postgres:root@localhost:5432/routing_db",
        algorithm="dijkstra",
        engine=cast(Any, fake_engine),
    )
    payload = RouteRequest(
        origin=GeoPoint(latitude=3.1390, longitude=101.6000),
        destination=GeoPoint(latitude=3.1410, longitude=101.6050),
    )
    response = await service.compute_route(payload)
    assert response.distance_meters == 5420.0
    assert response.eta_minutes == 12.5
    assert response.route_geojson["type"] == "FeatureCollection"
    assert len(response.route_geojson["features"]) == 1
    assert response.route_geojson["features"][0]["geometry"]["type"] == "LineString"


@pytest.mark.anyio
async def test_sql_routing_service_requires_destination() -> None:
    """Service should require destination coordinates for SQL backend mode."""
    service = SQLRoutingService(
        database_url="postgresql://postgres:root@localhost:5432/routing_db",
        algorithm="dijkstra",
        engine=cast(Any, _FakeEngine(rows=[])),
    )
    payload = RouteRequest(origin=GeoPoint(latitude=3.1390, longitude=101.6000))
    with pytest.raises(DomainValidationError) as exc:
        await service.compute_route(payload)
    assert exc.value.error_code == "VALIDATION_ERROR"


@pytest.mark.anyio
async def test_sql_routing_service_maps_no_route_to_not_found() -> None:
    """Service should map contract no route responses to "not found" errors."""
    service = SQLRoutingService(
        database_url="postgresql://postgres:root@localhost:5432/routing_db",
        algorithm="dijkstra",
        engine=cast(Any, _FakeEngine(rows=[(1001,), (2002,), None])),
    )
    payload = RouteRequest(
        origin=GeoPoint(latitude=3.1390, longitude=101.6000),
        destination=GeoPoint(latitude=3.1410, longitude=101.6050),
    )
    with pytest.raises(NotFoundError) as exc:
        await service.compute_route(payload)
    assert exc.value.error_code == "NOT_FOUND"


def test_sql_routing_service_maps_non_success_to_processing_error() -> None:
    """Service should map non route related contract errors to processing error."""
    service = SQLRoutingService(
        database_url="postgresql://postgres:root@localhost:5432/routing_db",
        algorithm="dijkstra",
        engine=cast(Any, _FakeEngine(rows=[])),
    )
    payload = RouteRequest(
        origin=GeoPoint(latitude=3.1390, longitude=101.6000),
        destination=GeoPoint(latitude=3.1410, longitude=101.6050),
    )
    with pytest.raises(ProcessingError) as exc:
        service._map_contract_result(
            payload=payload,
            result={"status": "error", "message": "database timeout"},
        )
    assert exc.value.error_code == "PROCESSING_ERROR"


@pytest.mark.anyio
async def test_sql_routing_service_rejects_invalid_numeric_fields() -> None:
    """Service should reject invalid numeric fields returned by contract."""
    service = SQLRoutingService(
        database_url="postgresql://postgres:root@localhost:5432/routing_db",
        algorithm="dijkstra",
        engine=cast(Any, _FakeEngine(rows=[])),
    )
    payload = RouteRequest(
        origin=GeoPoint(latitude=3.1390, longitude=101.6000),
        destination=GeoPoint(latitude=3.1410, longitude=101.6050),
    )
    with pytest.raises(ProcessingError) as exc:
        service._map_contract_result(
            payload=payload,
            result={
                "status": "success",
                "distance_km": "not-a-number",
                "eta_minutes": 2.0,
                "geojson": {"type": "FeatureCollection", "features": []},
            },
        )
    assert exc.value.error_code == "PROCESSING_ERROR"


@pytest.mark.anyio
async def test_sql_routing_service_rejects_invalid_geojson_shape() -> None:
    """Service should reject invalid geojson shape from contract."""
    service = SQLRoutingService(
        database_url="postgresql://postgres:root@localhost:5432/routing_db",
        algorithm="dijkstra",
        engine=cast(Any, _FakeEngine(rows=[])),
    )
    payload = RouteRequest(
        origin=GeoPoint(latitude=3.1390, longitude=101.6000),
        destination=GeoPoint(latitude=3.1410, longitude=101.6050),
    )
    with pytest.raises(ProcessingError) as exc:
        service._map_contract_result(
            payload=payload,
            result={
                "status": "success",
                "distance_km": 1.0,
                "eta_minutes": 2.0,
                "geojson": "invalid-geojson",
            },
        )
    assert exc.value.error_code == "PROCESSING_ERROR"


def test_route_endpoint_uses_sql_backend_when_configured(
    client,
    dependencies,
) -> None:
    """Endpoint should resolve SQL routing service when routing backend is sql."""
    fake_engine = _FakeEngine(
        rows=[
            (1001,),
            (2002,),
            (
                1000.0,
                120.0,
                '{"type":"LineString","coordinates":[[101.6869,3.139],[101.689,3.141]]}',
            ),
        ]
    )
    fake_sql_service = SQLRoutingService(
        database_url="postgresql://postgres:root@localhost:5432/routing_db",
        algorithm="dijkstra",
        engine=cast(Any, fake_engine),
    )
    original_get_settings = dependencies.get_settings
    original_sql_service = dependencies._sql_routing_service
    try:
        dependencies.get_settings = lambda: Settings(routing_backend="sql")
        dependencies._sql_routing_service = fake_sql_service
        response = client.get(
            "/api/v1/route?"
            "origin_lat=3.139&origin_lng=101.6&destination_lat=3.141&destination_lng=101.605"
        )
    finally:
        dependencies.get_settings = original_get_settings
        dependencies._sql_routing_service = original_sql_service

    assert response.status_code == 200
    payload = response.json()
    assert payload["distance_meters"] == 1000.0
    assert payload["eta_minutes"] == 2.0
