"""Login hardening: rate limiting, field limits, API key comparison."""
import pytest

import app.auth
from app.auth import LoginRateLimiter, hash_password, login_limiter
from app.config import settings


@pytest.fixture(autouse=True)
def reset_limiter():
    login_limiter.clear()
    yield
    login_limiter.clear()


@pytest.fixture
def auth_on(monkeypatch):
    monkeypatch.setattr(app.auth, "PBKDF2_ITERATIONS", 100_000)  # keep ~30 hashes fast
    monkeypatch.setattr(settings, "auth_enabled", True)
    monkeypatch.setattr(settings, "auth_username", "admin")
    monkeypatch.setattr(settings, "auth_password_hash", hash_password("pw"))


async def login(client, password="pw", username="admin"):
    return await client.post("/api/auth/login", json={"username": username, "password": password})


def test_limiter_blocks_after_threshold_and_expires():
    t = [0.0]
    limiter = LoginRateLimiter(max_failures=3, window_seconds=60, clock=lambda: t[0])
    for _ in range(3):
        limiter.record_failure("ip")
    assert limiter.retry_after("ip") > 0
    t[0] = 61
    assert limiter.retry_after("ip") == 0


def test_reset_clears_failures():
    limiter = LoginRateLimiter(max_failures=1, window_seconds=60)
    limiter.record_failure("ip")
    assert limiter.retry_after("ip") > 0
    limiter.reset("ip")
    assert limiter.retry_after("ip") == 0


async def test_login_locks_out_after_10_failures(client, auth_on):
    for _ in range(10):
        assert (await login(client, password="wrong")).status_code == 401
    response = await login(client)
    assert response.status_code == 429
    assert "retry-after" in response.headers


async def test_successful_login_resets(client, auth_on):
    for _ in range(9):
        assert (await login(client, password="wrong")).status_code == 401
    assert (await login(client)).status_code == 200
    for _ in range(9):
        assert (await login(client, password="wrong")).status_code == 401


async def test_wrong_username_rejected(client, auth_on):
    assert (await login(client, username="root")).status_code == 401


async def test_oversized_password_rejected(client, auth_on):
    assert (await login(client, password="x" * 1025)).status_code == 422


async def test_non_ascii_api_key_is_401(client, monkeypatch):
    monkeypatch.setattr(settings, "auth_enabled", True)
    monkeypatch.setattr(settings, "api_key", "abc")
    response = await client.get("/api/channels", headers=[(b"x-api-key", "é".encode("latin-1"))])
    assert response.status_code == 401


async def test_parallel_wrong_logins_capped_at_limit(client, auth_on):
    import asyncio
    responses = await asyncio.gather(*[login(client, password="wrong") for _ in range(40)])
    codes = [r.status_code for r in responses]
    assert codes.count(401) <= 10
    assert codes.count(429) >= 30
