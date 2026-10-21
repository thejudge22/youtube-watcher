"""
Importing videos by YouTube ID as saved videos (used by URL-list and playlist imports).

Rules:
- Never creates a Channel (subscription). A video is linked to a channel only if
  that channel is already subscribed; otherwise it keeps the copied channel info.
- Checks the database first and only fetches videos it doesn't already have.
"""
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.channel import Channel
from ..models.video import Video
from ..schemas.import_export import VideoImportResult
from .rss_parser import VideoInfo, fetch_video_by_id

logger = logging.getLogger(__name__)

# yt-dlp extractions running at once; higher values risk YouTube bot checks
IMPORT_CONCURRENCY = 4


async def import_videos_by_id(
    db: AsyncSession, youtube_video_ids: list[str], timeout: float
) -> VideoImportResult:
    """
    Save the given videos, fetching metadata only for ones not already in the database.

    Repeats of an ID within the same call count as skipped.
    """
    imported = 0
    skipped = 0
    errors: list[str] = []
    now = datetime.now(timezone.utc)

    unique_ids: list[str] = []
    seen: set[str] = set()
    for video_id in youtube_video_ids:
        if video_id in seen:
            skipped += 1
            continue
        seen.add(video_id)
        unique_ids.append(video_id)

    existing_result = await db.execute(select(Video).where(Video.youtube_video_id.in_(unique_ids)))
    existing = {video.youtube_video_id: video for video in existing_result.scalars().all()}
    for video in existing.values():
        if video.status != "saved":
            video.status = "saved"
            video.saved_at = now
            video.discarded_at = None
            imported += 1
        else:
            skipped += 1

    to_fetch = [video_id for video_id in unique_ids if video_id not in existing]
    semaphore = asyncio.Semaphore(IMPORT_CONCURRENCY)

    async def fetch_one(video_id: str) -> Optional[VideoInfo]:
        async with semaphore:
            try:
                return await fetch_video_by_id(video_id, timeout=timeout)
            except Exception as e:
                logger.warning(f"Failed to fetch video info for video_id={video_id}: {e}")
                return None

    fetched = await asyncio.gather(*[fetch_one(video_id) for video_id in to_fetch])

    infos: list[VideoInfo] = []
    for video_id, video_info in zip(to_fetch, fetched):
        if video_info is None:
            errors.append(f"Could not fetch video {video_id}")
        else:
            infos.append(video_info)

    channel_ids = {video_info.channel_id for video_info in infos if video_info.channel_id}
    subscriptions: dict[str, str] = {}
    if channel_ids:
        result = await db.execute(
            select(Channel.youtube_channel_id, Channel.id).where(Channel.youtube_channel_id.in_(channel_ids))
        )
        subscriptions = {row[0]: row[1] for row in result.all()}

    for video_info in infos:
        db.add(Video(
            youtube_video_id=video_info.video_id,
            channel_id=subscriptions.get(video_info.channel_id),
            channel_youtube_id=video_info.channel_id or None,
            channel_name=video_info.channel_name or None,
            channel_thumbnail_url=None,
            title=video_info.title,
            description=video_info.description or "",
            thumbnail_url=video_info.thumbnail_url,
            video_url=video_info.video_url,
            published_at=video_info.published_at,
            status="saved",
            saved_at=now,
            is_short=video_info.is_short,
        ))
        imported += 1

    await db.commit()
    logger.info(f"Import complete: {imported} imported, {skipped} skipped, {len(errors)} errors")

    return VideoImportResult(
        total=len(youtube_video_ids),
        imported=imported,
        skipped=skipped,
        errors=errors,
    )
