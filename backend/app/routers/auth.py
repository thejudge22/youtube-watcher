"""
Authentication router for Issue #41: Optional Authentication
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel

from ..auth import authenticate_user, create_access_token, verify_token
from ..config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


class AuthStatusResponse(BaseModel):
    """Response for auth status check."""
    enabled: bool


class LoginRequest(BaseModel):
    """Request body for login."""
    username: str
    password: str


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
async def login(request: LoginRequest):
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
    if not authenticate_user(request.username, request.password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
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
        { valid: true } if token is valid
        { valid: false } if token is invalid or expired
    """
    return TokenVerifyResponse(valid=verify_token(request.token))


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
