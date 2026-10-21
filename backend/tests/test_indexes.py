"""The list queries' composite indexes exist."""
from sqlalchemy import text


async def test_video_list_indexes_exist(db_session):
    result = await db_session.execute(
        text("select name from sqlite_master where type='index' and tbl_name='videos'")
    )
    names = set(result.scalars().all())
    assert {
        "ix_videos_status_published_at",
        "ix_videos_status_saved_at",
        "ix_videos_status_is_short_published_at",
    } <= names
