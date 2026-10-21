"""Unsubscribing: saved videos stay, inbox videos go to Recently Deleted."""
from datetime import datetime
from sqlalchemy import select, func
from app.models.channel import Channel
from app.models.video import Video
from tests.factories import make_channel, make_video, reload


async def test_unsubscribe_keeps_saved_and_discards_inbox(client, db_session):
    ch = make_channel()
    channel_id = ch.id
    common = dict(channel_id=channel_id, channel_youtube_id="UC-factory", channel_name="Factory Channel")
    saved = make_video(status="saved", **common)
    inbox = make_video(status="inbox", **common)
    old = make_video(status="discarded", discarded_at=datetime(2026, 1, 2), **common)
    saved_id, inbox_id, old_id = saved.id, inbox.id, old.id
    db_session.add(ch)
    db_session.add_all([saved, inbox, old])
    await db_session.commit()

    response = await client.delete(f"/api/channels/{channel_id}")
    assert response.status_code == 204

    assert await reload(db_session, Channel, channel_id) is None
    s = await reload(db_session, Video, saved_id)
    assert (s.status, s.channel_id, s.channel_youtube_id, s.channel_name) == ("saved", None, "UC-factory", "Factory Channel")
    assert s.saved_at is not None
    i = await reload(db_session, Video, inbox_id)
    assert (i.status, i.channel_id, i.saved_at) == ("discarded", None, None)
    assert i.discarded_at is not None
    o = await reload(db_session, Video, old_id)
    assert o.discarded_at == datetime(2026, 1, 2)
    remaining = await db_session.execute(select(func.count()).select_from(Video).where(Video.channel_id == channel_id))
    assert remaining.scalar_one() == 0


def test_channel_relationship_never_cascades_deletes():
    cascade = Channel.videos.property.cascade
    assert not cascade.delete and not cascade.delete_orphan
