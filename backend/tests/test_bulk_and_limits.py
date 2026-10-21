"""Bulk save/discard in one statement, and request size caps."""
from tests.factories import make_video

UUID = "00000000-0000-0000-0000-000000000000"


async def add_inbox_videos(db_session):
    videos = [make_video(status="inbox", channel_name="C") for _ in range(2)]
    ids = {video.id for video in videos}
    db_session.add_all(videos)
    await db_session.commit()
    return ids


async def test_bulk_save_updates_all(client, db_session):
    ids = await add_inbox_videos(db_session)
    response = await client.post("/api/videos/bulk-save", json={"video_ids": list(ids)})
    assert response.status_code == 200
    data = response.json()
    assert {v["id"] for v in data} == ids
    assert all(v["status"] == "saved" and v["channel_name"] == "C" for v in data)


async def test_bulk_discard_updates_all(client, db_session):
    ids = await add_inbox_videos(db_session)
    data = (await client.post("/api/videos/bulk-discard", json={"video_ids": list(ids)})).json()
    assert {v["id"] for v in data} == ids
    assert all(v["status"] == "discarded" and v["discarded_at"] is not None for v in data)


async def test_bulk_rejects_more_than_10000_ids(client):
    response = await client.post("/api/videos/bulk-save", json={"video_ids": [UUID] * 10001})
    assert response.status_code == 422


async def test_bulk_accepts_10000_ids(client):
    response = await client.post("/api/videos/bulk-save", json={"video_ids": [UUID] * 10000})
    assert response.status_code == 200
    assert response.json() == []


async def test_inbox_limit_capped(client):
    assert (await client.get("/api/videos/inbox?limit=10001")).status_code == 422
    assert (await client.get("/api/videos/inbox?limit=10000")).status_code == 200


async def test_import_urls_capped(client):
    urls = ["https://www.youtube.com/watch?v=aaaaaaaaaaa"] * 1001
    response = await client.post("/api/import-export/import/video-urls", json={"urls": urls})
    assert response.status_code == 422
