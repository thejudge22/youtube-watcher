from contextlib import asynccontextmanager
import os

from fastapi import FastAPI, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import AsyncSession

from .routers import channels, videos, import_export, settings, backup
from .database import get_db
from .models.setting import Setting
# Issue #12: Scheduled Backups
from .services.backup_scheduler import (
    start_scheduler,
    stop_scheduler,
    configure_backup_schedule,
    get_async_session
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure the data directory exists
    os.makedirs("data", exist_ok=True)

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
app.include_router(channels.router, prefix="/api")
app.include_router(videos.router, prefix="/api")
app.include_router(import_export.router, prefix="/api")
app.include_router(settings.router, prefix="/api")
# Issue #12: Scheduled Backups
app.include_router(backup.router, prefix="/api")

# This logic is for the production Docker container, where the frontend is built and served by FastAPI.
if os.path.exists("static"):
    app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # This will serve the index.html for any path that is not an API endpoint or a static asset.
        # This is necessary for single-page applications like React.
        if not full_path.startswith("api/"):
            return FileResponse("static/index.html")
