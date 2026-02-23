"""FastAPI exception handlers and registration."""

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.core.exceptions import AppError
from app.schemas.common import ErrorBody, ErrorResponse


def get_request_id(request: Request) -> str | None:
    """Extract request ID from request state when available."""
    return getattr(request.state, "request_id", None)


async def app_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle application exceptions."""
    assert isinstance(exc, AppError)
    payload = ErrorResponse(
        error=ErrorBody(
            code=exc.error_code,
            message=exc.message,
            details={
                "request_id": get_request_id(request),
                **exc.details,
            },
        )
    )
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


async def validation_exception_handler(
    request: Request, exc: Exception
) -> JSONResponse:
    """Handle pydantic validation errors."""
    assert isinstance(exc, RequestValidationError)
    payload = ErrorResponse(
        error=ErrorBody(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details={
                "request_id": get_request_id(request),
                "errors": exc.errors(),
            },
        )
    )
    return JSONResponse(status_code=422, content=payload.model_dump())


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle unknown/unexpected exceptions."""
    payload = ErrorResponse(
        error=ErrorBody(
            code="INTERNAL_SERVER_ERROR",
            message="An unexpected error occurred",
            details={
                "request_id": get_request_id(request),
                "type": exc.__class__.__name__,
            },
        )
    )
    return JSONResponse(status_code=500, content=payload.model_dump())


def register_exception_handlers(app: FastAPI) -> None:
    """Register all API exception handlers."""
    app.add_exception_handler(AppError, app_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)
