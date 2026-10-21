from contextlib import asynccontextmanager
import os
import logging
import mimetypes
from pathlib import Path

# Configure logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, Request
from starlette.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.cors import CORSMiddleware

# Ensure common MIME types are registered
mimetypes.add_type('image/png', '.png')
mimetypes.add_type('image/svg+xml', '.svg')
mimetypes.add_type('application/manifest+json', '.webmanifest')
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from .routers import channels, videos, import_export, settings, backup, auth, auto_refresh
from .auth import require_auth
from .config import settings as app_config
from .database import get_db
from .spa import register_frontend_routes
from .models.setting import Setting
# Issue #12: Scheduled Backups
from .services.backup_scheduler import (
    start_scheduler,
    stop_scheduler,
    configure_backup_schedule,
    get_async_session
)
# Issue #54: Auto-refresh
from .services.feed_refresh_scheduler import configure_auto_refresh_schedule
from .services.migration_runner import run_migrations


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure the data directory exists
    os.makedirs("data", exist_ok=True)

    # Run database migrations to ensure schema is up to date
    # This is critical for fresh installs
    await run_migrations()

    # Issue #12: Start the backup scheduler
    start_scheduler()

    # Load backup settings and configure schedule if enabled
    try:
        async with await get_async_session() as db:
            result = await db.execute(select(Setting).where(Setting.id == "1"))
            settings_obj = result.scalar_one_or_none()

            if settings_obj and settings_obj.backup_enabled:
                await configure_backup_schedule(
                    settings_obj.backup_schedule,
                    settings_obj.backup_time
                )

            # Issue #54: Configure auto-refresh if enabled
            if settings_obj and settings_obj.auto_refresh_enabled:
                await configure_auto_refresh_schedule(
                    settings_obj.auto_refresh_interval
                )
    except Exception as e:
        import logging
        logging.warning(f"Could not initialize backup schedule: {e}")

    yield

    # Shutdown: Stop scheduler
    stop_scheduler()


def api_docs_urls(auth_enabled: bool) -> dict[str, Optional[str]]:
    """Interactive API docs are only exposed when authentication is disabled."""
    if auth_enabled:
        return {"docs_url": None, "redoc_url": None, "openapi_url": None}
    return {"docs_url": "/docs", "redoc_url": "/redoc", "openapi_url": "/openapi.json"}


def parse_allowed_hosts(value: str) -> list[str]:
    """
    Parse ALLOWED_HOSTS (comma-separated). Empty means no Host check.

    localhost and 127.0.0.1 are always added so the container healthcheck works.
    """
    hosts = [h.strip() for h in value.split(",") if h.strip()]
    if not hosts:
        return []
    for required in ("localhost", "127.0.0.1"):
        if required not in hosts:
            hosts.append(required)
    return hosts


app = FastAPI(lifespan=lifespan, **api_docs_urls(app_config.auth_enabled))


@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers.setdefault("X-Content-Type-Options", "nosniff")
    response.headers.setdefault("X-Frame-Options", "DENY")
    response.headers.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    return response


# Optional Host header allow-list (blocks DNS-rebinding attacks); off unless ALLOWED_HOSTS is set
_allowed_hosts = parse_allowed_hosts(app_config.allowed_hosts)
if _allowed_hosts:
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=_allowed_hosts)

# Register exception handlers for consistent error responses
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from .exceptions import AppException
from .error_handlers import (
    app_exception_handler,
    http_exception_handler,
    validation_exception_handler,
    generic_exception_handler
)

app.add_exception_handler(AppException, app_exception_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# CORS Configuration - enabled in development or when CORS_ORIGINS is set
# In production (single container), CORS is not needed since API and frontend
# are served from the same origin
cors_origins_env = os.getenv("CORS_ORIGINS", "")
if os.getenv("ENV", "production") == "development" or cors_origins_env:
    origins = [
        "http://localhost:5173",
        "http://localhost:8000",
    ]
    if cors_origins_env:
        origins.extend([o.strip() for o in cors_origins_env.split(",") if o.strip()])

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.get("/api/health")
async def health(db: AsyncSession = Depends(get_db)):
    """
    Health check endpoint that verifies database connectivity.
    
    Returns:
        - 200 OK with status and database connection info on success
        - 503 Service Unavailable if database connection fails
    """
    try:
        await db.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected", "version": "2026-09-11", "api_version": "1"}
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail="Service unavailable: database connection failed"
        )

# Include routers
# Issue #41: Auth router (no auth required - needed for login)
app.include_router(auth.router, prefix="/api")

# Protected routers (auth required if AUTH_ENABLED=true)
app.include_router(channels.router, prefix="/api", dependencies=[Depends(require_auth)])
app.include_router(videos.router, prefix="/api", dependencies=[Depends(require_auth)])
app.include_router(import_export.router, prefix="/api", dependencies=[Depends(require_auth)])
app.include_router(settings.router, prefix="/api", dependencies=[Depends(require_auth)])
# Issue #12: Scheduled Backups
app.include_router(backup.router, prefix="/api", dependencies=[Depends(require_auth)])
# Issue #54: Auto-refresh
app.include_router(auto_refresh.router, prefix="/api", dependencies=[Depends(require_auth)])

# This logic is for the production Docker container, where the frontend is built and served by FastAPI.
if os.path.exists("static"):
    register_frontend_routes(app, Path("static"))
