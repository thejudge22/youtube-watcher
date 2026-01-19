from contextlib import asynccontextmanager
import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

from .routers import channels, videos, import_export, settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Ensure the data directory exists
    os.makedirs("data", exist_ok=True)
    yield
    # Shutdown: nothing to clean up


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
async def health():
    return {"status": "ok"}

# Include routers
app.include_router(channels.router, prefix="/api")
app.include_router(videos.router, prefix="/api")
app.include_router(import_export.router, prefix="/api")
app.include_router(settings.router, prefix="/api")

# This logic is for the production Docker container, where the frontend is built and served by FastAPI.
if os.path.exists("static"):
    app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # This will serve the index.html for any path that is not an API endpoint or a static asset.
        # This is necessary for single-page applications like React.
        if not full_path.startswith("api/"):
            return FileResponse("static/index.html")
