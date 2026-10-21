"""
Serving the built React frontend (SPA) from the production container.

All file lookups go through resolve_static_file() so a request path can never
escape the static directory (e.g. "/../data/youtube-watcher.db" or "//etc/passwd").
"""
import mimetypes
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles


def resolve_static_file(static_dir: Path, requested: str) -> Optional[Path]:
    """
    Resolve a requested path to a file inside static_dir.

    Returns None if the path escapes static_dir (via "..", an absolute path or a
    symlink), is not a regular file, or cannot be resolved.
    """
    try:
        root = static_dir.resolve()
        candidate = (root / requested).resolve()
    except (OSError, ValueError):
        return None
    if not candidate.is_relative_to(root) or not candidate.is_file():
        return None
    return candidate


def register_frontend_routes(app: FastAPI, static_dir: Path) -> None:
    """Mount the built frontend assets, PWA files and the SPA catch-all route."""
    app.mount("/assets", StaticFiles(directory=static_dir / "assets"), name="assets")

    # PWA: Serve service worker with correct MIME type and headers
    @app.api_route("/sw.js", methods=["GET", "HEAD"])
    async def serve_service_worker():
        return FileResponse(
            static_dir / "sw.js",
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
            static_dir / "manifest.webmanifest",
            media_type="application/manifest+json"
        )

    # PWA: Serve workbox script with correct MIME type
    @app.api_route("/workbox-{workbox_id}.js", methods=["GET", "HEAD"])
    async def serve_workbox(workbox_id: str):
        workbox_path = resolve_static_file(static_dir, f"workbox-{workbox_id}.js")
        if workbox_path is None:
            raise HTTPException(status_code=404, detail="Workbox script not found")
        return FileResponse(workbox_path, media_type="application/javascript")

    @app.api_route("/{full_path:path}", methods=["GET", "HEAD"])
    async def serve_spa(full_path: str):
        # Serve index.html for any path that is not an API endpoint or a static file.
        # This is necessary for single-page applications like React.
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found")
        static_file = resolve_static_file(static_dir, full_path)
        if static_file is not None:
            content_type, _ = mimetypes.guess_type(static_file.name)
            return FileResponse(static_file, media_type=content_type)
        return FileResponse(static_dir / "index.html")
