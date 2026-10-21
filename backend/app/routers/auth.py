"""
Authentication router for Issue #41: Optional Authentication
"""
import asyncio
import math
import time
from typing import Optional

from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field

from ..auth import (
    TOKEN_RENEW_AFTER_SECONDS,
    authenticate_user,
    create_access_token,
    get_token_payload,
    login_limiter,
)
from ..config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthStatusResponse(BaseModel):
    """Response for auth status check."""
    enabled: bool


class LoginRequest(BaseModel):
    """Request body for login."""
    username: str = Field(max_length=256)
    password: str = Field(max_length=1024)


class LoginResponse(BaseModel):
    """Response for successful login."""
    token: str
    token_type: str = "bearer"


class TokenVerifyRequest(BaseModel):
    """Request body for token verification."""
    token: str


class TokenVerifyResponse(BaseModel):
    """Response for token verification."""
    valid: bool
    # A renewed token when the current one is more than a day old (sliding sessions)
    token: Optional[str] = None


@router.get("/status", response_model=AuthStatusResponse)
async def get_auth_status():
    """
    Check if authentication is enabled.
    
    Frontend uses this on app startup to determine if login is required.
    
    Returns:
        { enabled: true } if auth is required
        { enabled: false } if no login needed
    """
    return AuthStatusResponse(enabled=settings.auth_enabled)


@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, http_request: Request):
    """
    Authenticate with username and password.
    
    Returns a JWT token on success that should be included in the
    Authorization header for subsequent requests.
    
    Args:
        request: Login credentials
        
    Returns:
        JWT token and token type
        
    Raises:
        HTTPException: 401 if credentials are invalid
    """
    key = http_request.client.host if http_request.client else "unknown"
    retry_after = login_limiter.retry_after(key)
    if retry_after > 0:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many failed login attempts. Try again later.",
            headers={"Retry-After": str(math.ceil(retry_after))},
        )

    # Count the attempt before checking it, so parallel requests can't all slip
    # past the limit while their hashes are still running; cleared on success.
    login_limiter.record_failure(key)

    # PBKDF2 is CPU-heavy; keep it off the event loop
    if not await asyncio.to_thread(authenticate_user, request.username, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    login_limiter.reset(key)
    token = create_access_token()
    return LoginResponse(token=token)


@router.post("/verify", response_model=TokenVerifyResponse)
async def verify_token_endpoint(request: TokenVerifyRequest):
    """
    Verify if a token is valid.
    
    Frontend uses this to check if a stored token is still valid.
    
    Args:
        request: Token to verify
        
    Returns:
        { valid: true, token: null } if token is valid
        { valid: true, token: <new token> } if valid and more than a day old
        { valid: false, token: null } if token is invalid or expired
    """
    payload = get_token_payload(request.token)
    if payload is None:
        return TokenVerifyResponse(valid=False)

    issued_at = float(payload["iat"])
    if time.time() - issued_at >= TOKEN_RENEW_AFTER_SECONDS:
        return TokenVerifyResponse(valid=True, token=create_access_token())
    return TokenVerifyResponse(valid=True)


@router.post("/logout")
async def logout():
    """
    Logout endpoint (client-side only).
    
    Since JWT tokens are stateless, logout is handled client-side
    by removing the token from storage. This endpoint exists for
    completeness and potential future server-side token blacklisting.
    
    Returns:
        Success message
    """
    return {"message": "Logout successful"}
