"""
Channel refresh service.

Issue #54: Extracted refresh logic for reuse by both the API router and the scheduler.
Issue #55: Added automatic Shorts detection during video imports.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import List, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..models.channel import Channel
from ..models.video import Video
from ..schemas.channel import RefreshSummary
from .rss_parser import fetch_videos, VideoInfo
from .settings_service import get_http_timeout, get_auto_detect_shorts
from .shorts_detector import detect_shorts_batch_http

logger = logging.getLogger(__name__)


async def process_new_videos(
    db: AsyncSession, channel: Channel, videos_info: List[VideoInfo]
) -> int:
    """
    Process new videos for a channel. Updates channel's last_checked and last_video_id.

    If auto_detect_shorts is enabled, runs HTTP-based shorts detection on new videos.

    Returns the number of new videos added.
    """
    new_videos_added = 0
    new_last_video_id = channel.last_video_id
    new_video_ids: list[str] = []

    for video_info in videos_info:
        # Stop if we've reached the last known video
        if video_info.video_id == channel.last_video_id:
            break

        # Check if video already exists
        existing = await db.execute(
            select(Video).where(Video.youtube_video_id == video_info.video_id)
        )
        if existing.scalar_one_or_none():
            continue

        # Create new video
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
        new_videos_added += 1
        new_video_ids.append(video_info.video_id)

        # Update last_video_id if this is the newest video
        if new_last_video_id is None or new_videos_added == 1:
            new_last_video_id = video_info.video_id

    # Update last_checked and last_video_id
    channel.last_checked = datetime.now(timezone.utc)
    if new_last_video_id:
        channel.last_video_id = new_last_video_id

    # Auto-detect shorts for new videos (Issue #55)
    if new_video_ids:
        await db.flush()  # Ensure new videos are in DB before UPDATE
        try:
            auto_detect = await get_auto_detect_shorts(db)
            if auto_detect:
                timeout = await get_http_timeout(db)
                results = await detect_shorts_batch_http(new_video_ids, timeout=timeout)
                now = datetime.now(timezone.utc)

                for vid, is_short in results.items():
                    if is_short is not None:
                        await db.execute(
                            Video.__table__.update()
                            .where(Video.youtube_video_id == vid)
                            .values(is_short=is_short, is_short_detected_at=now)
                        )
        except Exception as e:
            logger.warning(f"Auto shorts detection failed for channel {channel.id}: {e}")

    return new_videos_added


async def fetch_channel_videos(
    channel: Channel, timeout: float
) -> Tuple[Channel, List[VideoInfo] | None, str | None]:
    """
    Fetch videos for a channel. Returns (channel, videos_info, error).
    Error is None on success.
    """
    try:
        videos_info = await fetch_videos(channel.rss_url, limit=50, timeout=timeout)
        return (channel, videos_info, None)
    except Exception as e:
        return (channel, None, str(e))


async def refresh_all_channels(db: AsyncSession) -> RefreshSummary:
    """
    Refresh all channels and return a summary.

    Uses parallel fetching with a semaphore to limit concurrent requests.

    Returns:
        Summary with number of channels refreshed, new videos found, and any errors
    """
    # Get all channels
    result = await db.execute(select(Channel))
    channels = result.scalars().all()

    if not channels:
        return RefreshSummary(channels_refreshed=0, new_videos_found=0, errors=[])

    # Get timeout once for all requests
    timeout = await get_http_timeout(db)

    # Fetch all RSS feeds in parallel with concurrency limit
    semaphore = asyncio.Semaphore(5)

    async def fetch_with_semaphore(channel: Channel):
        async with semaphore:
            return await fetch_channel_videos(channel, timeout)

    fetch_results = await asyncio.gather(
        *[fetch_with_semaphore(channel) for channel in channels]
    )

    # Process results
    channels_refreshed = 0
    new_videos_found = 0
    errors = []

    for channel, videos_info, error in fetch_results:
        if error:
            errors.append(f"Channel '{channel.name}' (ID: {channel.id}): {error}")
            continue

        try:
            new_videos_added = await process_new_videos(db, channel, videos_info)
            channels_refreshed += 1
            new_videos_found += new_videos_added
        except Exception as e:
            errors.append(f"Channel '{channel.name}' (ID: {channel.id}): {str(e)}")

    # Commit all changes
    await db.commit()

    return RefreshSummary(
        channels_refreshed=channels_refreshed,
        new_videos_found=new_videos_found,
        errors=errors
    )