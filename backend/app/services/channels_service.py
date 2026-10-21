"""
Channel refresh service.

Issue #54: Extracted refresh logic for reuse by both the API router and the scheduler.
Issue #55: Added automatic Shorts detection during video imports.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple

import httpx

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.channel import Channel
from ..models.video import Video
from ..schemas.channel import RefreshSummary
from .rss_parser import fetch_videos, VideoInfo
from .settings_service import get_http_timeout, get_auto_detect_shorts
from .shorts_detector import detect_shorts_batch_http
from .youtube_utils import make_youtube_client

logger = logging.getLogger(__name__)


# Serializes feed refreshes (manual and scheduled) so two runs never insert the same video
refresh_lock = asyncio.Lock()


async def detect_and_store_shorts(db: AsyncSession, youtube_video_ids: list[str]) -> None:
    """
    Run HTTP-based Shorts detection for the given videos and store the results.

    No-op for an empty list or when auto-detection is disabled. Failures are
    logged, never raised: detection is best-effort.
    """
    if not youtube_video_ids:
        return
    try:
        if not await get_auto_detect_shorts(db):
            return
        timeout = await get_http_timeout(db)
        results = await detect_shorts_batch_http(youtube_video_ids, timeout=timeout)
        now = datetime.now(timezone.utc)
        for vid, is_short in results.items():
            if is_short is not None:
                await db.execute(
                    Video.__table__.update()
                    .where(Video.youtube_video_id == vid)
                    .values(is_short=is_short, is_short_detected_at=now)
                )
    except Exception as e:
        logger.warning(f"Auto shorts detection failed: {e}")


async def process_new_videos(
    db: AsyncSession, channel: Channel, videos_info: List[VideoInfo], *, detect_shorts: bool = True
) -> list[str]:
    """
    Add new feed videos for a channel to the inbox. Updates the channel's
    last_checked and last_video_id.

    If detect_shorts is set, runs Shorts detection on the new videos (callers that
    batch detection across channels pass False).
    Returns the YouTube IDs of the videos added.
    """
    feed_ids = [video_info.video_id for video_info in videos_info]
    existing_result = await db.execute(
        select(Video.youtube_video_id).where(Video.youtube_video_id.in_(feed_ids))
    )
    known_ids = set(existing_result.scalars().all())

    new_last_video_id = channel.last_video_id
    new_video_ids: list[str] = []

    for video_info in videos_info:
        # Stop if we've reached the last known video
        if video_info.video_id == channel.last_video_id:
            break

        # Skip videos already in the database (or repeated in this feed)
        if video_info.video_id in known_ids:
            continue
        known_ids.add(video_info.video_id)

        video = Video(
            youtube_video_id=video_info.video_id,
            channel_id=channel.id,
            channel_youtube_id=channel.youtube_channel_id,
            channel_name=channel.name,
            channel_thumbnail_url=channel.thumbnail_url,
            title=video_info.title,
            description=video_info.description,
            thumbnail_url=video_info.thumbnail_url,
            video_url=video_info.video_url,
            published_at=video_info.published_at,
            status='inbox'
        )
        db.add(video)
        new_video_ids.append(video_info.video_id)

        # The first new video is the newest one
        if len(new_video_ids) == 1:
            new_last_video_id = video_info.video_id

    # Update last_checked and last_video_id
    channel.last_checked = datetime.now(timezone.utc)
    if new_last_video_id:
        channel.last_video_id = new_last_video_id

    if new_video_ids:
        await db.flush()  # Ensure new videos are in DB before UPDATE
        if detect_shorts:
            await detect_and_store_shorts(db, new_video_ids)

    return new_video_ids


async def fetch_channel_videos(
    channel: Channel, timeout: float, client: Optional[httpx.AsyncClient] = None
) -> Tuple[Channel, List[VideoInfo] | None, str | None]:
    """
    Fetch videos for a channel. Returns (channel, videos_info, error).
    Error is None on success.
    """
    try:
        videos_info = await fetch_videos(channel.rss_url, limit=50, timeout=timeout, client=client)
        return (channel, videos_info, None)
    except Exception as e:
        return (channel, None, str(e))


async def refresh_all_channels(db: AsyncSession) -> RefreshSummary:
    """
    Refresh all channels and return a summary.

    Fetches feeds in parallel (semaphore-limited), processes them, then runs one
    batched Shorts detection for every new video. Runs under refresh_lock.

    Returns:
        Summary with number of channels refreshed, new videos found, and any errors
    """
    async with refresh_lock:
        result = await db.execute(select(Channel))
        channels = result.scalars().all()

        if not channels:
            return RefreshSummary(channels_refreshed=0, new_videos_found=0, errors=[])

        # Get timeout once for all requests
        timeout = await get_http_timeout(db)

        # Fetch all RSS feeds in parallel with concurrency limit
        semaphore = asyncio.Semaphore(5)

        async with make_youtube_client(timeout) as client:
            async def fetch_with_semaphore(channel: Channel):
                async with semaphore:
                    return await fetch_channel_videos(channel, timeout, client)

            fetch_results = await asyncio.gather(
                *[fetch_with_semaphore(channel) for channel in channels]
            )

        channels_refreshed = 0
        all_new_ids: list[str] = []
        errors = []

        for channel, videos_info, error in fetch_results:
            if error:
                errors.append(f"Channel '{channel.name}' (ID: {channel.id}): {error}")
                continue
            try:
                new_ids = await process_new_videos(db, channel, videos_info, detect_shorts=False)
                channels_refreshed += 1
                all_new_ids.extend(new_ids)
            except Exception as e:
                errors.append(f"Channel '{channel.name}' (ID: {channel.id}): {str(e)}")

        await detect_and_store_shorts(db, all_new_ids)
        await db.commit()

        return RefreshSummary(
            channels_refreshed=channels_refreshed,
            new_videos_found=len(all_new_ids),
            errors=errors
        )
