"""Shared API schema models."""

from typing import Any

from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    """Structured error payload for API responses."""

    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    """Wrapper schema for error responses."""

    error: ErrorBody


class HealthResponse(BaseModel):
    """Health/liveness response payload."""

    status: str = Field(examples=["ok"])
    service: str = Field(examples=["api"])
    version: str
    environment: str


class ApiInfoResponse(BaseModel):
    """Service metadata response payload."""

    service: str = Field(examples=["api"])
    message: str
