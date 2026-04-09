"""
Authentication module for optional login functionality.
Issue #41: Optional Authentication

Uses PBKDF2-SHA256 with Base64 encoding for compact, URL-safe hashes.
"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import base64
import hashlib
import secrets

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from .config import settings

# HTTP Bearer scheme for JWT token extraction
security = HTTPBearer(auto_error=False)

# PBKDF2 iteration count (higher = more secure but slower)
PBKDF2_ITERATIONS = 100000
# Salt size in bytes
SALT_SIZE = 16


def hash_password(password: str) -> str:
    """
    Hash a password using PBKDF2-SHA256 with a random salt.
    Returns URL-safe Base64 string (no padding, no special chars that cause shell issues)
    
    Args:
        password: The plain text password
        
    Returns:
        Base64url-encoded hash string (~64 characters)
    """
    # Generate a random salt
    salt = secrets.token_bytes(SALT_SIZE)
    # Hash the password (PBKDF2-SHA256 produces 32 bytes)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, PBKDF2_ITERATIONS)
    # Combine salt + hash and encode as URL-safe Base64 (no padding)
    combined = salt + pwdhash  # 16 + 32 = 48 bytes
    return base64.urlsafe_b64encode(combined).decode('ascii').rstrip('=')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a plain password against a PBKDF2 hash.
    
    Args:
        plain_password: The plain text password
        hashed_password: The Base64url-encoded hash (salt + hash)
        
    Returns:
        True if password matches, False otherwise
    """
    if not hashed_password:
        return False
    
    try:
        # Add padding back for base64 decoding (length should be ~64 chars for 48 bytes)
        padding_needed = (4 - len(hashed_password) % 4) % 4
        padded = hashed_password + ('=' * padding_needed)
        # Decode
        combined = base64.urlsafe_b64decode(padded.encode('ascii'))
        # Must be 48 bytes: 16 (salt) + 32 (hash)
        if len(combined) != SALT_SIZE + 32:
            return False
        # Extract salt and stored hash
        salt = combined[:SALT_SIZE]
        stored_hash = combined[SALT_SIZE:]
        # Hash the provided password with the same salt
        pwdhash = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, PBKDF2_ITERATIONS)
        # Compare using constant-time comparison to prevent timing attacks
        return secrets.compare_digest(pwdhash, stored_hash)
    except (ValueError, TypeError):
        # Invalid base64 or malformed hash
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
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> None:
    """
    FastAPI dependency to require authentication on protected routes.
    
    If AUTH_ENABLED is false, this allows all requests.
    If AUTH_ENABLED is true, requires a valid JWT token in the Authorization header.
    
    Args:
        credentials: The Authorization header credentials
        
    Raises:
        HTTPException: 401 if authentication is required but missing/invalid
    """
    # If auth is disabled, allow all requests
    if not settings.auth_enabled:
        return
    
    # Check for credentials
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify the token
    if not verify_token(credentials.credentials):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
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
