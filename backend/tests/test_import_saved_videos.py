"""JSON saved-video import links only existing subscriptions and never hits the network."""
from datetime import datetime
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select, func

from app.models.channel import Channel
from app.models.video import Video
from app.services.youtube_utils import get_video_url
from tests.factories import make_channel, make_video

E = "e" * 11
ENDPOINT = "/api/import-export/import/videos"


def item(**overrides):
    data = {"youtube_video_id": E, "title": "E", "video_url": get_video_url(E),
            "channel_youtube_id": "UC-unsub", "channel_name": "Unsub Channel", "channel_url": None,
            "saved_at": None, "published_at": "2026-01-01T00:00:00Z"}
    data.update(overrides)
    return data


@pytest.fixture(autouse=True)
def no_network(mocker):
    return mocker.patch("app.routers.import_export.fetch_channel_info",
                        AsyncMock(side_effect=AssertionError("network")))


async def get_video(db_session, youtube_video_id):
    db_session.expire_all()
    result = await db_session.execute(select(Video).where(Video.youtube_video_id == youtube_video_id))
    return result.scalar_one_or_none()


async def test_json_import_does_not_subscribe_or_fetch(client, db_session, no_network):
    data = (await client.post(ENDPOINT, json={"videos": [item()]})).json()
    no_network.assert_not_awaited()
    assert data["imported"] == 1
    assert (await db_session.execute(select(func.count()).select_from(Channel))).scalar_one() == 0
    video = await get_video(db_session, E)
    assert (video.channel_id, video.channel_name) == (None, "Unsub Channel")


async def test_json_import_links_existing_subscription(client, db_session):
    channel_youtube_id = "UC" + "s" * 22  # a real channel-ID shape (validated on import)
    channel = make_channel(youtube_channel_id=channel_youtube_id)
    channel_id = channel.id
    db_session.add(channel)
    await db_session.commit()
    await client.post(ENDPOINT, json={"videos": [item(channel_youtube_id=channel_youtube_id)]})
    assert (await get_video(db_session, E)).channel_id == channel_id


async def test_json_import_resaves_discarded(client, db_session):
    db_session.add(make_video(youtube_video_id=E, status="discarded", discarded_at=datetime(2026, 1, 2)))
    await db_session.commit()
    data = (await client.post(ENDPOINT, json={"videos": [item()]})).json()
    assert data["imported"] == 1
    video = await get_video(db_session, E)
    assert video.status == "saved"
    assert video.discarded_at is None


async def test_json_import_duplicate_items(client):
    data = (await client.post(ENDPOINT, json={"videos": [item(), item()]})).json()
    assert (data["imported"], data["skipped"], data["errors"]) == (1, 1, [])


async def test_json_import_beyond_sqlite_variable_limit(client, db_session):
    items = [item(youtube_video_id=f"{i:011d}") for i in range(40000)]
    data = (await client.post(ENDPOINT, json={"videos": items})).json()
    assert data["imported"] == 40000
