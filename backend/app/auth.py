"""
Authentication module for optional login functionality.
Issue #41: Optional Authentication

Uses versioned PBKDF2-SHA256 hashes (pbkdf2_sha256.<iterations>.<salt>.<hash>), URL-safe Base64.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import base64
import hashlib
import secrets

import jwt
from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import settings

# HTTP Bearer scheme for JWT token extraction
security = HTTPBearer(auto_error=False)

# PBKDF2 iteration count for new hashes (OWASP 2023 guidance for PBKDF2-SHA256)
PBKDF2_ITERATIONS = 600_000
# Iteration count of the original, unversioned hash format
LEGACY_PBKDF2_ITERATIONS = 100_000
# Accepted iteration range for versioned hashes
MIN_ITERATIONS = 100_000
MAX_ITERATIONS = 10_000_000
# Salt size in bytes
SALT_SIZE = 16
# Scheme prefix of the versioned format: pbkdf2_sha256.<iterations>.<salt>.<hash>
HASH_SCHEME = "pbkdf2_sha256"


def _b64encode(data: bytes) -> str:
    """URL-safe Base64 without padding (safe in .env files and shells)."""
    return base64.urlsafe_b64encode(data).decode('ascii').rstrip('=')


def _b64decode(text: str) -> bytes:
    padding_needed = (4 - len(text) % 4) % 4
    return base64.urlsafe_b64decode((text + '=' * padding_needed).encode('ascii'))


def hash_password(password: str) -> str:
    """
    Hash a password using PBKDF2-SHA256 with a random salt.

    Returns "pbkdf2_sha256.<iterations>.<salt>.<hash>" using only [A-Za-z0-9_.-],
    so it can be pasted into .env files and docker compose without escaping.
    """
    salt = secrets.token_bytes(SALT_SIZE)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, PBKDF2_ITERATIONS)
    return f"{HASH_SCHEME}.{PBKDF2_ITERATIONS}.{_b64encode(salt)}.{_b64encode(pwdhash)}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a stored hash.

    Accepts the versioned format from hash_password() and the legacy format
    (Base64 of 16-byte salt + 32-byte hash at 100k iterations).
    """
    if not hashed_password:
        return False

    try:
        if hashed_password.startswith(HASH_SCHEME + "."):
            parts = hashed_password.split(".")
            if len(parts) != 4:
                return False
            iterations = int(parts[1])
            if not MIN_ITERATIONS <= iterations <= MAX_ITERATIONS:
                return False
            salt = _b64decode(parts[2])
            stored_hash = _b64decode(parts[3])
        else:
            combined = _b64decode(hashed_password)
            # Must be 48 bytes: 16 (salt) + 32 (hash)
            if len(combined) != SALT_SIZE + 32:
                return False
            iterations = LEGACY_PBKDF2_ITERATIONS
            salt = combined[:SALT_SIZE]
            stored_hash = combined[SALT_SIZE:]

        pwdhash = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, iterations)
        # Compare using constant-time comparison to prevent timing attacks
        return secrets.compare_digest(pwdhash, stored_hash)
    except (ValueError, TypeError):
        # Invalid base64, iteration count or malformed hash
        return False


def create_access_token() -> str:
    """
    Create a JWT access token for authenticated sessions.
    
    Returns:
        JWT token string
    """
    expire = datetime.now(timezone.utc) + timedelta(hours=settings.jwt_expire_hours)
    payload = {
        "exp": expire,
        "iat": datetime.now(timezone.utc),
        "type": "access"
    }
    return jwt.encode(payload, settings.jwt_secret_key, algorithm="HS256")


def verify_token(token: str) -> bool:
    """
    Verify a JWT token is valid and not expired.
    
    Args:
        token: The JWT token to verify
        
    Returns:
        True if token is valid, False otherwise
    """
    try:
        jwt.decode(token, settings.jwt_secret_key, algorithms=["HS256"])
        return True
    except jwt.ExpiredSignatureError:
        return False
    except jwt.InvalidTokenError:
        return False


async def require_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
) -> None:
    """
    FastAPI dependency to require authentication on protected routes.

    If AUTH_ENABLED is false, this allows all requests.
    If AUTH_ENABLED is true, requires a valid JWT token in the Authorization header
    or a valid API key in the X-API-Key header.

    Args:
        credentials: The Authorization header credentials
        x_api_key: The X-API-Key header value

    Raises:
        HTTPException: 401 if authentication is required but missing/invalid
    """
    # If auth is disabled, allow all requests
    if not settings.auth_enabled:
        return

    # Check for API key first (programmatic access)
    if settings.api_key and x_api_key:
        if secrets.compare_digest(x_api_key, settings.api_key):
            return

    # Check for JWT token (browser session access)
    if credentials and verify_token(credentials.credentials):
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


def authenticate_user(username: str, password: str) -> bool:
    """
    Authenticate a user with username and password.
    
    Args:
        username: The username to authenticate
        password: The plain text password
        
    Returns:
        True if credentials are valid, False otherwise
    """
    if not settings.auth_enabled:
        return True
    
    if username != settings.auth_username:
        return False
    
    return verify_password(password, settings.auth_password_hash)
