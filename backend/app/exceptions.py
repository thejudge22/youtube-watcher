"""
Custom exception classes for consistent error handling.
"""
from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class AppException(HTTPException):
    """
    Base application exception with structured error information.

    All custom exceptions should inherit from this class.
    """

    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.code = code
        self.message = message
        self.details = details or {}
        # Call parent HTTPException with the message
        super().__init__(status_code=status_code, detail=message)


# Common exception classes for reuse

class NotFoundError(AppException):
    """Resource not found (404)."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            code=f"{resource.upper()}_NOT_FOUND",
            message=f"{resource} with ID {identifier} not found",
            details={"resource": resource, "id": identifier}
        )


class AlreadyExistsError(AppException):
    """Resource already exists (409)."""

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            code=f"{resource.upper()}_ALREADY_EXISTS",
            message=f"{resource} with ID {identifier} already exists",
            details={"resource": resource, "id": identifier}
        )


class ValidationError(AppException):
    """Validation failed (400)."""

    def __init__(self, message: str, field: Optional[str] = None):
        details = {"field": field} if field else {}
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            code="VALIDATION_ERROR",
            message=message,
            details=details
        )


class ExternalServiceError(AppException):
    """External service (YouTube, RSS) failed (502)."""

    def __init__(self, service: str, operation: str, error_message: str):
        super().__init__(
            status_code=status.HTTP_502_BAD_GATEWAY,
            code=f"{service.upper()}_ERROR",
            message=f"Failed to {operation}: {error_message}",
            details={"service": service, "operation": operation}
        )


class DatabaseError(AppException):
    """Database operation failed (500)."""

    def __init__(self, operation: str, error_message: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="DATABASE_ERROR",
            message=f"Database {operation} failed: {error_message}",
            details={"operation": operation}
        )
