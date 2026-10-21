"""Test data factories. Objects get explicit ids so tests can read them before committing."""
import uuid
from datetime import datetime, UTC
from app.models.channel import Channel
from app.models.video import Video
from app.services.youtube_utils import get_rss_url, get_channel_url, get_video_url

def make_channel(**overrides):
    cid = overrides.pop("youtube_channel_id", "UC-factory")
    data = dict(id=str(uuid.uuid4()), youtube_channel_id=cid, name="Factory Channel",
                rss_url=get_rss_url(cid), youtube_url=get_channel_url(cid))
    data.update(overrides)
    return Channel(**data)

def make_video(**overrides):
    vid = overrides.pop("youtube_video_id", uuid.uuid4().hex[:11])
    status = overrides.get("status", "saved")
    data = dict(id=str(uuid.uuid4()), youtube_video_id=vid, title="Video", video_url=get_video_url(vid),
                published_at=datetime(2026, 1, 1, tzinfo=UTC), status=status,
                saved_at=datetime.now(UTC) if status == "saved" else None)
    data.update(overrides)
    return Video(**data)

async def reload(session, model, id):
    """Re-read a row from the database, bypassing stale identity-map state."""
    session.expire_all()
    return await session.get(model, id)
