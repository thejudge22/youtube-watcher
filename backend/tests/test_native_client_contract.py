"""
Contract the native QuickPlay apps (macOS/iPad and Android) depend on.

Each test sends exactly the request the apps send. If one fails, the change breaks
installed apps: follow docs/native-clients.md (bump api_version, keep the old
behavior for a release, update the apps first) instead of editing the test.
"""
from datetime import datetime, UTC
from unittest.mock import AsyncMock

import pytest

from app.config import settings
from app.services.rss_parser import VideoInfo
from app.services.youtube_utils import get_video_url
from tests.factories import make_channel, make_video

API_KEY = "native-client-test-key"

# Video fields the apps decode: non-null with a fixed JSON type, or nullable strings
VIDEO_REQUIRED = {"id": str, "youtube_video_id": str, "title": str, "video_url": str,
                  "published_at": str, "status": str, "is_short": bool}
VIDEO_NULLABLE = ["channel_id", "channel_youtube_id", "channel_name", "channel_thumbnail_url",
                  "description", "thumbnail_url", "saved_at", "discarded_at", "is_short_detected_at"]

SAVED_QUERY = "sort_by=published_at&order=asc&limit=50&offset=0"
INBOX_PATH = "/api/videos/inbox?limit=10000&offset=0"


def assert_video(video: dict) -> None:
    for field, kind in VIDEO_REQUIRED.items():
        assert isinstance(video.get(field), kind), f"{field} must be a non-null {kind.__name__}"
    for field in VIDEO_NULLABLE:
        assert field in video, f"{field} must be present (null allowed)"
        assert video[field] is None or isinstance(video[field], str), f"{field} must be a string or null"
    assert video["status"] in ("inbox", "saved", "discarded")
    assert video["published_at"].endswith("Z")
    assert video["video_url"].startswith("https://www.youtube.com/")


@pytest.fixture
async def library(db_session):
    """A subscribed channel with two inbox videos and saved videos/Shorts, some unsubscribed."""
    channel = make_channel()
    db_session.add(channel)
    rows = [
        make_video(status="inbox", channel_id=channel.id, channel_name="Factory Channel",
                   published_at=datetime(2026, 1, 2, tzinfo=UTC)),
        make_video(status="inbox", channel_id=channel.id, channel_name="Factory Channel", is_short=True,
                   published_at=datetime(2026, 1, 1, tzinfo=UTC)),
        make_video(status="saved", channel_id=channel.id, published_at=datetime(2025, 5, 1, tzinfo=UTC)),
        make_video(status="saved", published_at=datetime(2025, 3, 1, 12, 30, tzinfo=UTC)),  # unsubscribed
        make_video(status="saved", is_short=True, published_at=datetime(2025, 4, 1, tzinfo=UTC)),
    ]
    ids = {"inbox": [rows[0].id, rows[1].id], "saved": [rows[2].id, rows[3].id], "short": rows[4].id}
    db_session.add_all(rows)
    await db_session.commit()
    return ids


async def test_health_shape(client):
    response = await client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert isinstance(data["version"], str)
    assert data["api_version"] == "1"


@pytest.mark.parametrize("is_short", ["false", "true"])
async def test_saved_page_shape_and_order(client, library, is_short):
    response = await client.get(f"/api/videos/saved?is_short={is_short}&{SAVED_QUERY}")
    assert response.status_code == 200
    page = response.json()
    assert set(page) >= {"videos", "total", "limit", "offset", "has_more"}
    assert isinstance(page["total"], int) and isinstance(page["has_more"], bool)
    assert page["limit"] == 50 and page["offset"] == 0
    for video in page["videos"]:
        assert_video(video)
        assert video["status"] == "saved"
        assert video["is_short"] is (is_short == "true")
    dates = [v["published_at"] for v in page["videos"]]
    assert dates == sorted(dates)
    assert len(page["videos"]) == (1 if is_short == "true" else 2)


async def test_unsubscribed_saved_video_has_null_channel_id(client, library):
    page = (await client.get(f"/api/videos/saved?is_short=false&{SAVED_QUERY}")).json()
    assert page["videos"][0]["channel_id"] is None


async def test_inbox_is_a_plain_list_oldest_first(client, library):
    response = await client.get(INBOX_PATH)
    assert response.status_code == 200
    videos = response.json()
    assert isinstance(videos, list)
    assert [v["id"] for v in videos] == list(reversed(library["inbox"]))
    for video in videos:
        assert_video(video)
        assert video["status"] == "inbox"


@pytest.mark.parametrize("action,status", [("save", "saved"), ("discard", "discarded")])
async def test_single_actions_return_video(client, library, action, status):
    response = await client.post(f"/api/videos/{library['inbox'][0]}/{action}")
    assert response.status_code == 200
    assert_video(response.json())
    assert response.json()["status"] == status


@pytest.mark.parametrize("action,status", [("bulk-save", "saved"), ("bulk-discard", "discarded")])
async def test_bulk_actions_return_videos(client, library, action, status):
    response = await client.post(f"/api/videos/{action}", json={"video_ids": library["inbox"]})
    assert response.status_code == 200
    videos = response.json()
    assert {v["id"] for v in videos} == set(library["inbox"])
    for video in videos:
        assert_video(video)
        assert video["status"] == status


async def test_quickplay_removal_via_bulk_discard_is_restorable(client, library):
    ids = library["saved"]
    await client.post("/api/videos/bulk-discard", json={"video_ids": ids})
    restored = (await client.post("/api/videos/bulk-save", json={"video_ids": ids})).json()
    assert {v["status"] for v in restored} == {"saved"}


async def test_delete_returns_204_with_empty_body(client, library):
    response = await client.delete(f"/api/videos/{library['short']}")
    assert response.status_code == 204
    assert response.content == b""


async def test_from_url_201_then_200(client, mocker):
    video_id = "dQw4w9WgXcQ"
    mocker.patch("app.routers.videos.fetch_video_by_id", AsyncMock(return_value=VideoInfo(
        video_id=video_id, channel_id="UC-x", channel_name="X", title="T",
        video_url=get_video_url(video_id), published_at=datetime(2026, 1, 1, tzinfo=UTC))))
    body = {"url": f"https://www.youtube.com/watch?v={video_id}"}

    first = await client.post("/api/videos/from-url", json=body)
    second = await client.post("/api/videos/from-url", json=body)

    assert (first.status_code, second.status_code) == (201, 200)
    assert_video(first.json())
    assert first.json()["id"] == second.json()["id"]
    assert second.json()["status"] == "saved"


async def test_refresh_all_summary_shape(client, db_session, mocker):
    db_session.add(make_channel())
    await db_session.commit()
    mocker.patch("app.services.channels_service.fetch_videos", AsyncMock(side_effect=RuntimeError("feed down")))
    mocker.patch("app.services.channels_service.detect_shorts_batch_http", AsyncMock(return_value={}))

    response = await client.post("/api/channels/refresh-all")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data["channels_refreshed"], int)
    assert isinstance(data["new_videos_found"], int)
    assert isinstance(data["errors"], list) and len(data["errors"]) == 1


async def test_error_envelope(client):
    response = await client.post("/api/videos/00000000-0000-0000-0000-000000000000/save")
    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "VIDEO_NOT_FOUND"
    assert isinstance(error["message"], str)


@pytest.fixture
def auth_with_key(monkeypatch):
    monkeypatch.setattr(settings, "auth_enabled", True)
    monkeypatch.setattr(settings, "api_key", API_KEY)


NATIVE_REQUESTS = [
    ("GET", f"/api/videos/saved?is_short=false&{SAVED_QUERY}", None),
    ("GET", INBOX_PATH, None),
    ("POST", "/api/videos/bulk-save", {"video_ids": []}),
    ("POST", "/api/videos/bulk-discard", {"video_ids": []}),
]


async def test_open_endpoints_need_no_key(client, auth_with_key):
    assert (await client.get("/api/health", headers={"X-API-Key": "wrong"})).status_code == 200
    status = await client.get("/api/auth/status")
    assert status.status_code == 200 and status.json()["enabled"] is True


@pytest.mark.parametrize("method,path,body", NATIVE_REQUESTS)
async def test_api_key_accepted(client, auth_with_key, method, path, body):
    response = await client.request(method, path, json=body, headers={"X-API-Key": API_KEY})
    assert response.status_code == 200


@pytest.mark.parametrize("headers", [{}, {"X-API-Key": "wrong"}])
@pytest.mark.parametrize("method,path,body", NATIVE_REQUESTS)
async def test_missing_or_wrong_key_is_401(client, auth_with_key, method, path, body, headers):
    response = await client.request(method, path, json=body, headers=headers)
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
