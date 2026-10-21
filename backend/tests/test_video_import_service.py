"""URL-list and playlist imports: never subscribe, check the DB first, validate playlist URLs."""
from datetime import datetime, UTC
from unittest.mock import AsyncMock

import pytest
from sqlalchemy import select, func

from app.models.channel import Channel
from app.models.video import Video
from app.services.rss_parser import VideoInfo
from app.services.youtube_utils import get_video_url
from tests.factories import make_video

A, B, C, D = "a" * 11, "b" * 11, "c" * 11, "d" * 11
URL_ENDPOINT = "/api/import-export/import/video-urls"
PLAYLIST_ENDPOINT = "/api/import-export/import/playlist"


def info(video_id, channel_id="UC-unsub", channel_name="Unsub Channel") -> VideoInfo:
    return VideoInfo(video_id=video_id, channel_id=channel_id, channel_name=channel_name,
                     title=f"T {video_id}", video_url=get_video_url(video_id),
                     published_at=datetime(2026, 1, 1, tzinfo=UTC))


@pytest.fixture
def fetch(mocker):
    return mocker.patch("app.services.video_import_service.fetch_video_by_id",
                        AsyncMock(side_effect=lambda vid, timeout: info(vid)))


async def get_video(db_session, youtube_video_id):
    db_session.expire_all()
    result = await db_session.execute(select(Video).where(Video.youtube_video_id == youtube_video_id))
    return result.scalar_one_or_none()


async def test_url_import_does_not_subscribe(client, db_session, fetch):
    response = await client.post(URL_ENDPOINT, json={"urls": [get_video_url(A)]})
    assert response.json()["imported"] == 1
    assert (await db_session.execute(select(func.count()).select_from(Channel))).scalar_one() == 0
    video = await get_video(db_session, A)
    assert (video.channel_id, video.channel_youtube_id, video.channel_name, video.status) == (
        None, "UC-unsub", "Unsub Channel", "saved")


async def test_url_import_links_existing_subscription(client, db_session, sample_channel, fetch):
    sample_id = sample_channel.id
    fetch.side_effect = lambda vid, timeout: info(vid, channel_id="UC-test123")
    await client.post(URL_ENDPOINT, json={"urls": [get_video_url(A)]})
    assert (await get_video(db_session, A)).channel_id == sample_id


async def test_url_import_resaves_existing_without_fetch(client, db_session, fetch):
    db_session.add(make_video(youtube_video_id=B, status="discarded", discarded_at=datetime(2026, 1, 2)))
    await db_session.commit()

    response = await client.post(URL_ENDPOINT, json={"urls": [get_video_url(B)]})

    fetch.assert_not_awaited()
    assert response.json()["imported"] == 1
    video = await get_video(db_session, B)
    assert video.status == "saved"
    assert video.discarded_at is None


async def test_url_import_duplicates_invalid_and_blank(client, fetch):
    urls = [get_video_url(A), get_video_url(A), "https://example.com/x", ""]
    data = (await client.post(URL_ENDPOINT, json={"urls": urls})).json()
    assert (data["total"], data["imported"], data["skipped"]) == (4, 1, 1)
    assert data["errors"] == ["Invalid YouTube URL: https://example.com/x"]
    assert fetch.await_count == 1


async def test_url_import_reports_fetch_failure(client, fetch):
    fetch.side_effect = ValueError("gone")
    data = (await client.post(URL_ENDPOINT, json={"urls": [get_video_url(C)]})).json()
    assert data["errors"] == [f"Could not fetch video {C}"]


async def test_playlist_rejects_non_youtube_url(client, mocker):
    playlist = mocker.patch("app.routers.import_export.fetch_playlist_video_ids", AsyncMock())
    response = await client.post(PLAYLIST_ENDPOINT, json={"url": "http://169.254.169.254/latest"})
    assert response.status_code == 200
    assert response.json()["errors"][0].startswith("Unrecognized YouTube playlist URL format")
    playlist.assert_not_awaited()


async def test_playlist_uses_canonical_url(client, mocker, fetch):
    playlist = mocker.patch("app.routers.import_export.fetch_playlist_video_ids",
                            AsyncMock(return_value=[D]))
    response = await client.post(
        PLAYLIST_ENDPOINT, json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PL123abc"})
    assert playlist.await_args.args[0] == "https://www.youtube.com/playlist?list=PL123abc"
    assert response.json()["imported"] == 1
