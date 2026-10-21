"""Tests for the read-only settings getters (fresh installs have no settings row)."""
from sqlalchemy import select, func

from app.models.setting import Setting
from app.services.settings_service import get_http_timeout, get_auto_detect_shorts


async def test_http_timeout_default_without_row_does_not_write(db_session):
    assert await get_http_timeout(db_session) == 10.0
    assert (await db_session.execute(select(func.count()).select_from(Setting))).scalar_one() == 0


async def test_auto_detect_shorts_default_without_row(db_session):
    assert await get_auto_detect_shorts(db_session) is True


async def test_create_channel_invalid_url_on_fresh_db(client):
    response = await client.post("/api/channels", json={"url": "https://example.com/bad"})
    assert response.status_code == 400
