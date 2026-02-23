"""Shared API schema models."""

from typing import Any

from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    code: str
    message: str
    details: dict[str, Any] | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


class HealthResponse(BaseModel):
    status: str = Field(examples=["ok"])
    service: str = Field(examples=["api"])
    version: str
    environment: str


class ApiInfoResponse(BaseModel):
    service: str = Field(examples=["api"])
    message: str
