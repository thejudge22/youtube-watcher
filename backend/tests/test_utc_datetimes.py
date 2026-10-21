"""API datetimes are serialized as UTC."""
from datetime import datetime, timedelta, timezone

from app.schemas.types import ensure_utc


async def test_video_datetimes_have_utc_suffix(client, sample_video):
    data = (await client.get("/api/videos/inbox")).json()
    assert data[0]["published_at"].endswith("Z")


def test_ensure_utc():
    assert ensure_utc(datetime(2026, 1, 1)).tzinfo == timezone.utc
    six_ahead = datetime(2026, 1, 1, 6, tzinfo=timezone(timedelta(hours=6)))
    assert ensure_utc(six_ahead) == datetime(2026, 1, 1, tzinfo=timezone.utc)
