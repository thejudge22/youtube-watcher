"""Password hashing: versioned PBKDF2 format with legacy support."""
import base64
import hashlib
import re
import secrets
import subprocess

import pytest

from app.auth import hash_password, verify_password


def legacy_hash(password: str) -> str:
    """Hash exactly as the original generate-password-hash.sh did (100k iterations)."""
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100000)
    return base64.urlsafe_b64encode(salt + digest).decode("ascii").rstrip("=")


def test_hash_roundtrip():
    h = hash_password("pw")
    assert verify_password("pw", h)
    assert not verify_password("nope", h)


def test_hash_format():
    h = hash_password("pw")
    assert h.split(".")[:2] == ["pbkdf2_sha256", "600000"]
    assert re.fullmatch(r"[A-Za-z0-9_.\-]+", h)


def test_legacy_hash_still_verifies():
    assert verify_password("pw", legacy_hash("pw"))


@pytest.mark.parametrize("bad", ["", "pbkdf2_sha256.abc.x.y", "pbkdf2_sha256.50.x.y", "!!!"])
def test_malformed_hashes_rejected(bad):
    assert not verify_password("pw", bad)


def test_script_output_verifies():
    result = subprocess.run(["bash", "../scripts/generate-password-hash.sh", "s3cret"],
                            capture_output=True, text=True, check=True)
    value = result.stdout.rsplit("AUTH_PASSWORD_HASH=", 1)[1].split()[0]
    assert verify_password("s3cret", value)
