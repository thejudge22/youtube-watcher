"""Tests for SPA/static file serving (path traversal protection)."""
import asyncio
from pathlib import Path

import pytest
from fastapi import FastAPI

from app.spa import resolve_static_file, register_frontend_routes


async def raw_get(app, path: str) -> tuple[int, bytes]:
    """Send a GET with an un-normalized path straight to the ASGI app."""
    scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": "GET",
             "scheme": "http", "path": path, "raw_path": path.encode(), "query_string": b"",
             "headers": [], "server": ("test", 80), "client": ("test", 1), "root_path": ""}
    messages, sent = [], False

    async def receive():
        nonlocal sent
        if not sent:
            sent = True
            return {"type": "http.request", "body": b"", "more_body": False}
        await asyncio.Event().wait()  # never disconnect

    async def send(message):
        messages.append(message)

    await app(scope, receive, send)
    status = next(m["status"] for m in messages if m["type"] == "http.response.start")
    body = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
    return status, body


@pytest.fixture
def site(tmp_path):
    static = tmp_path / "static"
    (static / "assets").mkdir(parents=True)
    (static / "index.html").write_text("SPA")
    (static / "favicon.ico").write_text("ICON")
    (tmp_path / "secret.txt").write_text("SECRET")
    app = FastAPI()
    register_frontend_routes(app, static)
    return tmp_path, static, app


def test_resolve_returns_file_inside_static(site):
    _, static, _ = site
    assert resolve_static_file(static, "favicon.ico") == (static / "favicon.ico").resolve()


def test_resolve_rejects_parent_traversal(site):
    _, static, _ = site
    assert resolve_static_file(static, "../secret.txt") is None


def test_resolve_rejects_absolute_path(site):
    tmp_path, static, _ = site
    assert resolve_static_file(static, str(tmp_path / "secret.txt")) is None


def test_resolve_rejects_directory_and_missing(site):
    _, static, _ = site
    assert resolve_static_file(static, "assets") is None
    assert resolve_static_file(static, "nope.txt") is None


def test_resolve_rejects_symlink_escape(site):
    tmp_path, static, _ = site
    (static / "link.txt").symlink_to(tmp_path / "secret.txt")
    assert resolve_static_file(static, "link.txt") is None


async def test_spa_serves_index_for_routes(site):
    _, _, app = site
    assert await raw_get(app, "/inbox") == (200, b"SPA")


async def test_spa_serves_static_file(site):
    _, _, app = site
    assert await raw_get(app, "/favicon.ico") == (200, b"ICON")


async def test_spa_blocks_traversal(site):
    tmp_path, _, app = site
    for path in ["/../secret.txt", "//etc/hosts", "/" + str(tmp_path) + "/secret.txt"]:
        assert await raw_get(app, path) == (200, b"SPA"), path


async def test_unknown_api_path_is_404(site):
    _, _, app = site
    assert (await raw_get(app, "/api/nope"))[0] == 404
