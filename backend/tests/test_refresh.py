"""Feed refresh: batched queries and shorts detection, serialized runs, honest status."""
from datetime import datetime, UTC
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select, func

from app.models.channel import Channel
from app.models.video import Video
from app.schemas.channel import RefreshSummary
from app.services import channels_service
from app.services.channels_service import process_new_videos
from app.services.feed_refresh_scheduler import summarize_refresh_outcome
from app.services.rss_parser import VideoInfo
from app.services.youtube_utils import get_video_url
from tests.factories import make_channel, make_video, reload


def vid(n: int) -> str:
    return "v" + str(n).zfill(10)


def info(video_id: str) -> VideoInfo:
    return VideoInfo(video_id=video_id, channel_id="UC-factory", channel_name="Factory Channel",
                     title=f"T {video_id}", video_url=get_video_url(video_id),
                     published_at=datetime(2026, 1, 1, tzinfo=UTC))


@pytest.fixture
def shorts(mocker):
    return mocker.patch("app.services.channels_service.detect_shorts_batch_http", AsyncMock(return_value={}))


async def test_process_new_videos_stops_at_last_known_and_skips_existing(db_session, shorts):
    ch = make_channel(last_video_id=vid(3))
    channel_id = ch.id
    db_session.add(ch)
    db_session.add(make_video(youtube_video_id=vid(2)))
    await db_session.commit()

    channel = await reload(db_session, Channel, channel_id)
    feed = [info(vid(1)), info(vid(2)), info(vid(3)), info(vid(4))]
    new_ids = await process_new_videos(db_session, channel, feed, detect_shorts=False)
    await db_session.commit()

    assert new_ids == [vid(1)]
    assert (await reload(db_session, Channel, channel_id)).last_video_id == vid(1)
    count = await db_session.execute(select(func.count()).select_from(Video).where(Video.youtube_video_id == vid(1)))
    assert count.scalar_one() == 1
    shorts.assert_not_awaited()


async def test_refresh_all_detects_shorts_once_for_all_channels(client, db_session, mocker, shorts):
    first = make_channel(youtube_channel_id="UC-one")
    second = make_channel(youtube_channel_id="UC-two")
    feeds = {first.rss_url: [info(vid(1))], second.rss_url: [info(vid(2))]}
    db_session.add_all([first, second])
    await db_session.commit()

    async def fake_fetch(rss_url, *args, **kwargs):
        return feeds[rss_url]

    mocker.patch("app.services.channels_service.fetch_videos", side_effect=fake_fetch)
    data = (await client.post("/api/channels/refresh-all")).json()

    assert data["new_videos_found"] == 2
    shorts.assert_awaited_once()
    assert set(shorts.await_args.args[0]) == {vid(1), vid(2)}


async def test_refresh_all_holds_lock(client, db_session, mocker, shorts):
    db_session.add(make_channel())
    await db_session.commit()

    async def fake_fetch(rss_url, *args, **kwargs):
        assert channels_service.refresh_lock.locked()
        return []

    mocker.patch("app.services.channels_service.fetch_videos", side_effect=fake_fetch)
    response = await client.post("/api/channels/refresh-all")
    assert response.status_code == 200
    assert response.json()["channels_refreshed"] == 1


async def test_refresh_channel_holds_lock(client, db_session, mocker, shorts):
    ch = make_channel()
    channel_id = ch.id
    db_session.add(ch)
    await db_session.commit()

    async def fake_fetch(rss_url, *args, **kwargs):
        assert channels_service.refresh_lock.locked()
        return []

    mocker.patch("app.routers.channels.fetch_videos", side_effect=fake_fetch)
    response = await client.post(f"/api/channels/{channel_id}/refresh")
    assert response.status_code == 200


@pytest.mark.parametrize("refreshed, errors, expected", [
    (2, [], ("success", None)),
    (2, ["X"], ("success", "1 channel(s) failed. First error: X")),
    (0, ["X", "Y"], ("failed", "2 channel(s) failed. First error: X")),
])
def test_summarize_refresh_outcome(refreshed, errors, expected):
    summary = RefreshSummary(channels_refreshed=refreshed, new_videos_found=0, errors=errors)
    assert summarize_refresh_outcome(summary) == expected
