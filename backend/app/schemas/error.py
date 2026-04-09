"""
Error response schemas for consistent API error handling.
"""
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel, ConfigDict


class ErrorDetail(BaseModel):
    """Detailed error information."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "code": "CHANNEL_NOT_FOUND",
            "message": "Channel with ID abc-123 not found",
            "details": {"channel_id": "abc-123"}
        }
    })

    code: str  # Machine-readable error code (e.g., "CHANNEL_NOT_FOUND")
    message: str  # Human-readable error message
    details: Optional[Dict[str, Any]] = None  # Additional error context


class ErrorResponse(BaseModel):
    """Standard error response format for all API errors."""

    model_config = ConfigDict(json_schema_extra={
        "example": {
            "error": {
                "code": "CHANNEL_NOT_FOUND",
                "message": "Channel with ID abc-123 not found",
                "details": {"channel_id": "abc-123"}
            },
            "timestamp": "2026-01-18T17:00:00Z",
            "path": "/api/channels/abc-123",
            "status_code": 404
        }
    })

    error: ErrorDetail
    timestamp: datetime
    path: str
    status_code: int
