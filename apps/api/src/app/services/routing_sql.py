"""SQL-backed routing service integrating Member C's route contract."""

from __future__ import annotations

from asyncio import to_thread
from typing import Any

from routing.sql.contract import get_route
from routing.sql.engine import create_routing_engine
from sqlalchemy.engine import Engine

from app.core.exceptions import (
    DomainValidationError,
    ExternalServiceError,
    NotFoundError,
    ProcessingError,
)
from app.schemas.routing import RouteRequest, RouteResponse


class SQLRoutingService:
    """Routing service backed by Member C contract query module."""

    def __init__(
        self,
        *,
        database_url: str,
        algorithm: str = "dijkstra",
        engine: Engine | None = None,
    ) -> None:
        """Initialize SQL routing service options and contract dependencies."""
        normalized_algorithm = algorithm.lower()
        if normalized_algorithm not in {"dijkstra", "astar"}:
            raise DomainValidationError(
                message="routing algorithm must be one of: dijkstra, astar",
                field="routing_algorithm",
            )

        self._database_url = database_url
        self._algorithm = normalized_algorithm
        self._engine = engine or create_routing_engine(database_url)

    async def compute_route(self, payload: RouteRequest) -> RouteResponse:
        """Compute route from origin to destination using contract module."""
        return await to_thread(self._compute_route_sync, payload)

    def _compute_route_sync(self, payload: RouteRequest) -> RouteResponse:
        """Call contract and map the output to public API response schema."""
        destination = payload.destination
        if destination is None:
            raise DomainValidationError(
                message=(
                    "destination coordinates are required when ROUTING_BACKEND=sql"
                ),
                field="destination",
            )

        try:
            result = get_route(
                start_lat=payload.origin.latitude,
                start_lon=payload.origin.longitude,
                end_lat=destination.latitude,
                end_lon=destination.longitude,
                algorithm=self._algorithm,
                engine=self._engine,
            )
        except ValueError as exc:
            raise DomainValidationError(
                message=str(exc),
                field="routing_algorithm",
            ) from exc
        except RuntimeError as exc:
            raise ExternalServiceError(
                service="routing-db",
                message=str(exc),
                details={"database_url": self._database_url},
            ) from exc
        except Exception as exc:
            raise ExternalServiceError(
                service="routing-contract",
                message="routing contract execution failed",
            ) from exc

        return self._map_contract_result(payload=payload, result=result)

    def _map_contract_result(
        self,
        *,
        payload: RouteRequest,
        result: dict[str, Any],
    ) -> RouteResponse:
        """Map routing contract output to the public route response schema."""
        status = str(result.get("status", "")).lower()
        if status != "success":
            message = str(result.get("message", "routing contract returned error"))
            resource_id = (
                f"{payload.origin.latitude},{payload.origin.longitude}->"
                f"{payload.destination.latitude if payload.destination else 'unknown'},"
                f"{payload.destination.longitude if payload.destination else 'unknown'}"
            )
            if "snap" in message.lower() or "no route" in message.lower():
                raise NotFoundError(resource="route", resource_id=resource_id)
            raise ProcessingError(
                message="routing contract returned non-success result",
                details={"contract_message": message},
            )

        try:
            distance_km = float(result.get("distance_km", 0.0))
            eta_minutes = float(result.get("eta_minutes", 0.0))
        except (TypeError, ValueError) as exc:
            raise ProcessingError(
                message="routing contract returned invalid numeric fields",
                details={"result": result},
            ) from exc

        route_feature = result.get("geojson")
        if route_feature is None:
            route_geojson = {"type": "FeatureCollection", "features": []}
        elif isinstance(route_feature, dict) and route_feature.get("type") == "Feature":
            route_geojson = {"type": "FeatureCollection", "features": [route_feature]}
        elif (
            isinstance(route_feature, dict)
            and route_feature.get("type") == "FeatureCollection"
        ):
            route_geojson = route_feature
        else:
            raise ProcessingError(
                message="routing contract returned invalid geojson shape",
                details={"geojson": route_feature},
            )

        return RouteResponse(
            route_geojson=route_geojson,
            distance_meters=round(distance_km * 1000.0, 2),
            eta_minutes=round(eta_minutes, 2),
        )
