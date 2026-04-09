"""
Global exception handlers for consistent error responses.
"""
from datetime import datetime, timezone
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .exceptions import AppException
from .schemas.error import ErrorResponse, ErrorDetail


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom AppException instances."""
    error_response = ErrorResponse(
        error=ErrorDetail(
            code=exc.code,
            message=exc.message,
            details=exc.details
        ),
        timestamp=datetime.now(timezone.utc),
        path=str(request.url.path),
        status_code=exc.status_code
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode='json')
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Handle standard HTTPException instances (fallback for unconverted exceptions)."""
    # Determine error code from status code
    code_map = {
        400: "BAD_REQUEST",
        401: "UNAUTHORIZED",
        403: "FORBIDDEN",
        404: "NOT_FOUND",
        409: "CONFLICT",
        422: "UNPROCESSABLE_ENTITY",
        500: "INTERNAL_SERVER_ERROR",
        502: "BAD_GATEWAY",
        503: "SERVICE_UNAVAILABLE"
    }

    error_response = ErrorResponse(
        error=ErrorDetail(
            code=code_map.get(exc.status_code, "HTTP_ERROR"),
            message=str(exc.detail),
            details={}
        ),
        timestamp=datetime.now(timezone.utc),
        path=str(request.url.path),
        status_code=exc.status_code
    )

    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode='json')
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Handle Pydantic validation errors."""
    # Format validation errors into details
    validation_details = {}
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error["loc"])
        validation_details[field] = error["msg"]

    error_response = ErrorResponse(
        error=ErrorDetail(
            code="VALIDATION_ERROR",
            message="Request validation failed",
            details={"validation_errors": validation_details}
        ),
        timestamp=datetime.now(timezone.utc),
        path=str(request.url.path),
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=error_response.model_dump(mode='json')
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all handler for unexpected exceptions."""
    # Log the full exception for debugging
    import traceback
    print("Unexpected error:", traceback.format_exc())

    error_response = ErrorResponse(
        error=ErrorDetail(
            code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            details={}  # Don't expose internal error details in production
        ),
        timestamp=datetime.now(timezone.utc),
        path=str(request.url.path),
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_response.model_dump(mode='json')
    )
