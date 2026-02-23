"""Custom exception types for the backend API."""

from typing import Any


class AppError(Exception):
    """Base exception for API domain and service errors."""

    def __init__(
        self,
        message: str,
        *,
        error_code: str = "APP_ERROR",
        status_code: int = 400,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a base application exception payload."""
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}


class NotFoundError(AppError):
    """Raised when a resource cannot be found."""

    def __init__(
        self,
        resource: str,
        resource_id: Any,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize not-found metadata for the missing resource."""
        super().__init__(
            message=f"{resource} with id '{resource_id}' not found",
            error_code="NOT_FOUND",
            status_code=404,
            details={
                "resource": resource,
                "resource_id": str(resource_id),
                **(details or {}),
            },
        )


class DomainValidationError(AppError):
    """Raised for domain-level validation issues."""

    def __init__(
        self,
        message: str,
        field: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a domain validation failure payload."""
        merged_details = {"field": field, **(details or {})} if field else details
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            status_code=400,
            details=merged_details,
        )


class ProcessingError(AppError):
    """Raised for internal processing failures."""

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a processing failure payload."""
        super().__init__(
            message=message,
            error_code="PROCESSING_ERROR",
            status_code=500,
            details=details,
        )


class ExternalServiceError(AppError):
    """Raised for downstream service failures."""

    def __init__(
        self,
        service: str,
        message: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """Initialize a downstream service failure payload."""
        super().__init__(
            message=f"{service} error: {message}",
            error_code="EXTERNAL_SERVICE_ERROR",
            status_code=502,
            details={"service": service, **(details or {})},
        )
