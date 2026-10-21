"""JWT secret persistence and token claims."""
import stat
from datetime import datetime, timedelta, timezone

import jwt
import pytest

import app.auth
from app.auth import create_access_token, get_jwt_secret, verify_token
from app.config import settings


@pytest.fixture(autouse=True)
def secret_file(tmp_path, monkeypatch):
    path = tmp_path / "data" / ".jwt_secret"
    monkeypatch.setattr(app.auth, "JWT_SECRET_FILE", path)
    monkeypatch.setattr(app.auth, "_jwt_secret", None)
    monkeypatch.setattr(settings, "jwt_secret_key", "")
    return path


def test_secret_generated_once_and_persisted(secret_file):
    first = get_jwt_secret()
    assert get_jwt_secret() == first
    assert secret_file.read_text().strip() == first
    assert stat.S_IMODE(secret_file.stat().st_mode) == 0o600
    app.auth._jwt_secret = None  # simulated restart
    assert get_jwt_secret() == first


def test_env_secret_takes_precedence(secret_file, monkeypatch):
    monkeypatch.setattr(settings, "jwt_secret_key", "fixed")
    assert get_jwt_secret() == "fixed"
    assert not secret_file.exists()


def test_token_roundtrip():
    assert verify_token(create_access_token())


def _encode(payload: dict) -> str:
    return jwt.encode(payload, get_jwt_secret(), algorithm="HS256")


def test_wrong_type_rejected():
    now = datetime.now(timezone.utc)
    token = _encode({"type": "refresh", "iat": now, "exp": now + timedelta(hours=1)})
    assert not verify_token(token)


def test_missing_iat_rejected():
    now = datetime.now(timezone.utc)
    token = _encode({"type": "access", "exp": now + timedelta(hours=1)})
    assert not verify_token(token)


def make_token(age_hours: float) -> str:
    issued = datetime.now(timezone.utc) - timedelta(hours=age_hours)
    return _encode({"type": "access", "iat": issued, "exp": issued + timedelta(hours=336)})


async def test_verify_fresh_token_not_renewed(client):
    response = await client.post("/api/auth/verify", json={"token": make_token(1)})
    assert response.json() == {"valid": True, "token": None}


async def test_verify_day_old_token_renewed(client):
    old = make_token(25)
    data = (await client.post("/api/auth/verify", json={"token": old})).json()
    assert data["valid"] is True
    assert isinstance(data["token"], str) and data["token"]
    assert verify_token(data["token"])
    unverified = {"verify_signature": False}
    assert jwt.decode(data["token"], options=unverified)["exp"] > jwt.decode(old, options=unverified)["exp"]


async def test_verify_garbage_token(client):
    response = await client.post("/api/auth/verify", json={"token": "garbage"})
    assert response.json() == {"valid": False, "token": None}


def test_token_survives_restart():
    token = create_access_token()
    app.auth._jwt_secret = None  # simulated restart; the secret file remains
    assert verify_token(token)
