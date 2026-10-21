"""
Authentication module for optional login functionality.
Issue #41: Optional Authentication

Uses versioned PBKDF2-SHA256 hashes (pbkdf2_sha256.<iterations>.<salt>.<hash>), URL-safe Base64.
"""
from datetime import datetime, timedelta, timezone
import base64
import os
import hashlib
import secrets
import time
from pathlib import Path
from typing import Callable, Optional

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


# Where a generated JWT secret is kept when JWT_SECRET_KEY isn't set (relative to the app's working directory)
JWT_SECRET_FILE = Path("data") / ".jwt_secret"
_jwt_secret: Optional[str] = None
# Sliding sessions: /api/auth/verify issues a fresh token once the current one is this old
TOKEN_RENEW_AFTER_SECONDS = 24 * 3600


def get_jwt_secret() -> str:
    """
    Return the JWT signing secret.

    Precedence: JWT_SECRET_KEY from the environment; else the secret stored in
    JWT_SECRET_FILE; else a new random secret, written there once (mode 0600) so
    sessions survive restarts.
    """
    global _jwt_secret
    if settings.jwt_secret_key:
        return settings.jwt_secret_key
    if _jwt_secret:
        return _jwt_secret

    path = JWT_SECRET_FILE
    if path.exists():
        stored = path.read_text().strip()
        if stored:
            _jwt_secret = stored
            return _jwt_secret
        # A blank file (e.g. a crash mid-write) would make every login fail; replace it
        path.unlink(missing_ok=True)

    secret = secrets.token_urlsafe(32)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    except FileExistsError:
        # Another process created it first; use theirs if it has been written
        stored = path.read_text().strip()
        if not stored:
            raise RuntimeError(f"JWT secret file {path} is empty; delete it and restart")
        _jwt_secret = stored
        return _jwt_secret
    with os.fdopen(fd, "w") as f:
        f.write(secret)
    _jwt_secret = secret
    return _jwt_secret


def create_access_token() -> str:
    """
    Create a JWT access token for authenticated sessions.

    Returns:
        JWT token string
    """
    now = datetime.now(timezone.utc)
    payload = {
        "exp": now + timedelta(hours=settings.jwt_expire_hours),
        "iat": now,
        "type": "access"
    }
    return jwt.encode(payload, get_jwt_secret(), algorithm="HS256")


def get_token_payload(token: str) -> Optional[dict]:
    """
    Decode a token, returning its payload only if it is a valid, unexpired
    access token (signature, exp, iat and type all check out); else None.
    """
    try:
        payload = jwt.decode(
            token, get_jwt_secret(), algorithms=["HS256"], options={"require": ["exp", "iat"]}
        )
    except jwt.InvalidTokenError:
        return None
    if payload.get("type") != "access":
        return None
    return payload


def verify_token(token: str) -> bool:
    """True if token is a valid, unexpired access token."""
    return get_token_payload(token) is not None


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
        # Compare bytes: compare_digest raises on non-ASCII str input
        if secrets.compare_digest(x_api_key.encode(), settings.api_key.encode()):
            return

    # Check for JWT token (browser session access)
    if credentials and verify_token(credentials.credentials):
        return

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required",
        headers={"WWW-Authenticate": "Bearer"},
    )


class LoginRateLimiter:
    """
    In-memory limiter for failed logins, keyed by client IP.

    A key is blocked once it has max_failures failures within window_seconds.
    Behind a reverse proxy all clients may share one IP, so a lockout then
    applies to everyone until the window passes.
    """

    def __init__(
        self,
        max_failures: int = 10,
        window_seconds: float = 900.0,
        clock: Callable[[], float] = time.monotonic,
    ):
        self.max_failures = max_failures
        self.window_seconds = window_seconds
        self._clock = clock
        self._failures: dict[str, list[float]] = {}

    def _recent(self, key: str) -> list[float]:
        cutoff = self._clock() - self.window_seconds
        recent = [t for t in self._failures.get(key, []) if t > cutoff]
        if recent:
            self._failures[key] = recent
        else:
            self._failures.pop(key, None)
        return recent

    def retry_after(self, key: str) -> float:
        """Seconds until key may try again (0.0 when not blocked)."""
        recent = self._recent(key)
        if len(recent) < self.max_failures:
            return 0.0
        return max(0.0, recent[0] + self.window_seconds - self._clock())

    def record_failure(self, key: str) -> None:
        self._recent(key)
        self._failures.setdefault(key, []).append(self._clock())

    def reset(self, key: str) -> None:
        self._failures.pop(key, None)

    def clear(self) -> None:
        self._failures.clear()


login_limiter = LoginRateLimiter()


def authenticate_user(username: str, password: str) -> bool:
    """
    Authenticate a user with username and password.

    Always checks both the username (constant-time) and the password, so timing
    doesn't reveal whether the username was right.

    Args:
        username: The username to authenticate
        password: The plain text password

    Returns:
        True if credentials are valid, False otherwise
    """
    if not settings.auth_enabled:
        return True

    user_ok = secrets.compare_digest(username.encode(), settings.auth_username.encode())
    password_ok = verify_password(password, settings.auth_password_hash)
    return user_ok and password_ok
