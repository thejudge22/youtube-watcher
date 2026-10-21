"""Imports validate IDs and rebuild URLs instead of trusting the file."""
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select, func

from app.models.channel import Channel
from app.models.video import Video
from app.services.rss_parser import ChannelInfo

CID = "UC" + "a" * 22
H = "h" * 11


@pytest.fixture
def channel_fetch(mocker):
    return mocker.patch("app.routers.import_export.fetch_channel_info",
                        AsyncMock(return_value=ChannelInfo(channel_id=CID, name="N")))


def item(**overrides):
    data = {"youtube_video_id": H, "title": "H", "video_url": f"https://www.youtube.com/watch?v={H}",
            "channel_youtube_id": None, "channel_name": "Some Channel", "channel_url": None,
            "saved_at": None, "published_at": None}
    data.update(overrides)
    return data


async def stored_videos(db_session):
    db_session.expire_all()
    return (await db_session.execute(select(Video))).scalars().all()


async def test_import_video_ignores_supplied_url(client, db_session):
    await client.post("/api/import-export/import/videos", json={"videos": [item(video_url="javascript:alert(1)")]})
    [video] = await stored_videos(db_session)
    assert video.video_url == "https://www.youtube.com/watch?v=hhhhhhhhhhh"


async def test_import_video_rejects_invalid_id(client, db_session):
    data = (await client.post("/api/import-export/import/videos",
                              json={"videos": [item(youtube_video_id='x"><img src=x>')]})).json()
    assert data["imported"] == 0
    assert data["errors"] == ["Invalid video ID: 'x\"><img src=x>'"]
    assert await stored_videos(db_session) == []


async def test_import_video_drops_invalid_channel_id(client, db_session):
    await client.post("/api/import-export/import/videos", json={"videos": [item(channel_youtube_id="not-a-channel")]})
    [video] = await stored_videos(db_session)
    assert video.channel_youtube_id is None
    assert video.channel_name == "Some Channel"


async def test_import_channel_ignores_supplied_url(client, db_session, channel_fetch):
    await client.post("/api/import-export/import/channels", json={"channels": [
        {"youtube_channel_id": CID, "name": "N", "youtube_url": "javascript:alert(1)"}]})
    db_session.expire_all()
    channel = (await db_session.execute(select(Channel))).scalar_one()
    assert channel.youtube_url == f"https://www.youtube.com/channel/{CID}"


async def test_import_channel_rejects_invalid_id(client, db_session, channel_fetch):
    data = (await client.post("/api/import-export/import/channels", json={"channels": [
        {"youtube_channel_id": "UCshort", "name": "N", "youtube_url": "x"}]})).json()
    assert data["errors"] == ["Invalid channel ID for N: 'UCshort'"]
    channel_fetch.assert_not_awaited()
    assert (await db_session.execute(select(func.count()).select_from(Channel))).scalar_one() == 0
