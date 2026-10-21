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
