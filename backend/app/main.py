from contextlib import asynccontextmanager
import os
import logging
import mimetypes

# Configure logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# Ensure common MIME types are registered
mimetypes.add_type('image/png', '.png')
mimetypes.add_type('image/svg+xml', '.svg')
mimetypes.add_type('application/manifest+json', '.webmanifest')
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from .routers import channels, videos, import_export, settings, backup, auth
from .auth import require_auth
from .database import get_db
from .models.setting import Setting
# Issue #12: Scheduled Backups
from .services.backup_scheduler import (
    start_scheduler,
    stop_scheduler,
    configure_backup_schedule,
    get_async_session
)
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
    except Exception as e:
        import logging
        logging.warning(f"Could not initialize backup schedule: {e}")

    yield

    # Shutdown: Stop scheduler
    stop_scheduler()


app = FastAPI(lifespan=lifespan)

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

# CORS Configuration - only for development
# In production (single container), CORS is not needed since API and frontend
# are served from the same origin
if os.getenv("ENV", "production") == "development":
    origins = [
        "http://localhost:5173",
        "http://localhost:8000",
    ]

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
        return {"status": "ok", "database": "connected"}
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

# This logic is for the production Docker container, where the frontend is built and served by FastAPI.
if os.path.exists("static"):
    app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")
    
    # PWA: Serve service worker with correct MIME type and headers
    @app.api_route("/sw.js", methods=["GET", "HEAD"])
    async def serve_service_worker():
        return FileResponse(
            "static/sw.js",
            media_type="application/javascript",
            headers={
                "Cache-Control": "no-cache",  # Don't cache the service worker
                "Service-Worker-Allowed": "/",  # Allow service worker to control all paths
            }
        )
    
    # PWA: Serve web manifest with correct MIME type
    @app.api_route("/manifest.webmanifest", methods=["GET", "HEAD"])
    async def serve_manifest():
        return FileResponse(
            "static/manifest.webmanifest",
            media_type="application/manifest+json"
        )
    
    # PWA: Serve workbox script with correct MIME type
    @app.api_route("/workbox-{workbox_id}.js", methods=["GET", "HEAD"])
    async def serve_workbox(workbox_id: str):
        workbox_path = f"static/workbox-{workbox_id}.js"
        if os.path.isfile(workbox_path):
            return FileResponse(workbox_path, media_type="application/javascript")
        raise HTTPException(status_code=404, detail="Workbox script not found")
    
    @app.api_route("/{full_path:path}", methods=["GET", "HEAD"])
    async def serve_spa(full_path: str):
        # This will serve the index.html for any path that is not an API endpoint or a static asset.
        # This is necessary for single-page applications like React.
        if not full_path.startswith("api/"):
            # Check if the requested file exists in the static directory (e.g., favicon.jpg)
            static_file_path = os.path.join("static", full_path)
            if os.path.isfile(static_file_path):
                # Detect MIME type based on file extension
                content_type, _ = mimetypes.guess_type(static_file_path)
                return FileResponse(static_file_path, media_type=content_type)
            return FileResponse("static/index.html")
