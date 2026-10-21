"""API docs gating, security headers and the optional host allow-list."""
from app.main import api_docs_urls, parse_allowed_hosts


def test_docs_hidden_when_auth_enabled():
    assert all(value is None for value in api_docs_urls(True).values())


def test_docs_shown_when_auth_disabled():
    assert api_docs_urls(False)["docs_url"] == "/docs"


async def test_security_headers_present(client):
    response = await client.get("/api/health")
    assert response.headers["x-content-type-options"] == "nosniff"
    assert response.headers["x-frame-options"] == "DENY"
    assert response.headers["referrer-policy"] == "strict-origin-when-cross-origin"


def test_parse_allowed_hosts():
    assert parse_allowed_hosts("") == []
    assert parse_allowed_hosts("  ") == []
    assert parse_allowed_hosts("a.example, b.example") == ["a.example", "b.example", "localhost", "127.0.0.1"]
    assert parse_allowed_hosts("localhost") == ["localhost", "127.0.0.1"]
