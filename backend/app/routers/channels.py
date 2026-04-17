"""
Channel management API router.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from datetime import datetime, timezone
from typing import List, Dict

from ..database import get_db
from ..models.channel import Channel
from ..models.video import Video
from ..schemas.channel import ChannelCreate, ChannelResponse, RefreshSummary
from ..services.youtube_utils import extract_channel_id, get_rss_url, get_channel_url
from ..services.rss_parser import fetch_channel_info, fetch_videos
from ..services.settings_service import get_http_timeout, get_auto_detect_shorts
from ..services.channels_service import process_new_videos, fetch_channel_videos, refresh_all_channels as refresh_all_channels_service
from ..services.shorts_detector import detect_shorts_batch_http
from ..exceptions import NotFoundError, AlreadyExistsError, ValidationError, ExternalServiceError

router = APIRouter()

logger = logging.getLogger(__name__)


async def get_video_counts_for_channels(db: AsyncSession, channel_ids: List[str]) -> Dict[str, int]:
    """Get the count of inbox and saved videos for multiple channels in a single query."""
    if not channel_ids:
        return {}

    result = await db.execute(
        select(Video.channel_id, func.count(Video.id))
        .where(Video.channel_id.in_(channel_ids))
        .where(Video.status.in_(["inbox", "saved"]))
        .group_by(Video.channel_id)
    )
    return {row[0]: row[1] for row in result.all()}


async def get_video_count(db: AsyncSession, channel_id: str) -> int:
    """Get the count of inbox and saved videos for a channel."""
    result = await db.execute(
        select(func.count(Video.id))
        .where(Video.channel_id == channel_id)
        .where(Video.status.in_(["inbox", "saved"]))
    )
    return result.scalar() or 0


def channel_to_response_with_count(channel: Channel, video_count: int) -> ChannelResponse:
    """Convert a Channel model to ChannelResponse with pre-computed video count."""
    return ChannelResponse(
        id=channel.id,
        youtube_channel_id=channel.youtube_channel_id,
        name=channel.name,
        youtube_url=channel.youtube_url,
        thumbnail_url=channel.thumbnail_url,
        last_checked=channel.last_checked,
        video_count=video_count
    )


async def channel_to_response(db: AsyncSession, channel: Channel) -> ChannelResponse:
    """Convert a Channel model to ChannelResponse with video count."""
    video_count = await get_video_count(db, channel.id)
    return channel_to_response_with_count(channel, video_count)


@router.get("/channels", response_model=List[ChannelResponse])
async def list_channels(db: AsyncSession = Depends(get_db)):
    """
    List all channels with video counts.
    """
    result = await db.execute(select(Channel).order_by(func.lower(Channel.name)))
    channels = result.scalars().all()

    # Get all video counts in a single query
    channel_ids = [channel.id for channel in channels]
    video_counts = await get_video_counts_for_channels(db, channel_ids)

    return [
        channel_to_response_with_count(channel, video_counts.get(channel.id, 0))
        for channel in channels
    ]


@router.post("/channels", response_model=ChannelResponse, status_code=status.HTTP_201_CREATED)
async def create_channel(channel_data: ChannelCreate, db: AsyncSession = Depends(get_db)):
    """
    Add a new channel and fetch its last 15 videos.

    Logic:
    1. Extract channel ID from URL
    2. Check if channel already exists (return error if so)
    3. Fetch channel info (name, thumbnail)
    4. Fetch last 15 videos from RSS
    5. Create channel record
    6. Create video records with status='inbox'
    7. Return channel with video count
    """
    # Step 1: Extract channel ID
    timeout = await get_http_timeout(db)
    try:
        youtube_channel_id = await extract_channel_id(channel_data.url, timeout=timeout)
    except ValueError as e:
        raise ValidationError(str(e), field="url")

    # Step 2: Check if channel already exists
    existing = await db.execute(
        select(Channel).where(Channel.youtube_channel_id == youtube_channel_id)
    )
    if existing.scalar_one_or_none():
        raise AlreadyExistsError("Channel", youtube_channel_id)

    # Step 3: Fetch channel info
    try:
        channel_info = await fetch_channel_info(youtube_channel_id, timeout=timeout)
    except Exception as e:
        raise ExternalServiceError("YouTube", "fetch channel info", str(e))

    # Step 4: Fetch last 15 videos
    rss_url = get_rss_url(youtube_channel_id)
    try:
        videos_info = await fetch_videos(rss_url, limit=15, timeout=timeout)
    except Exception as e:
        raise ExternalServiceError("YouTube", "fetch videos", str(e))

    # Step 5: Create channel record
    channel = Channel(
        youtube_channel_id=youtube_channel_id,
        name=channel_info.name,
        rss_url=rss_url,
        youtube_url=get_channel_url(youtube_channel_id),
        thumbnail_url=channel_info.thumbnail_url,
        last_checked=datetime.now(timezone.utc),
        last_video_id=videos_info[0].video_id if videos_info else None
    )
    db.add(channel)
    await db.flush()  # Flush to get the channel ID

    # Step 6: Create video records with status='inbox'
    new_video_ids: list[str] = []
    for video_info in videos_info:
        # Skip if video already exists (may have been added via another channel)
        existing = await db.execute(
            select(Video).where(Video.youtube_video_id == video_info.video_id)
        )
        if existing.scalar_one_or_none():
            continue

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

    # Auto-detect shorts for new videos (Issue #55)
    if new_video_ids:
        await db.flush()  # Ensure new videos are in DB before UPDATE
        try:
            auto_detect = await get_auto_detect_shorts(db)
            if auto_detect:
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
            logger.warning(f"Auto shorts detection failed for new channel: {e}")

    await db.commit()
    await db.refresh(channel)

    # Step 7: Return channel with video count
    return await channel_to_response(db, channel)


@router.delete("/channels/{channel_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_channel(
    channel_id: str = Path(..., pattern="^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a channel and all its videos.

    The cascade delete on the foreign key will automatically delete all videos
    associated with this channel.
    """
    # Check if channel exists
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()

    if not channel:
        raise NotFoundError("Channel", channel_id)

    # Delete the channel (cascade will delete videos)
    await db.execute(delete(Channel).where(Channel.id == channel_id))
    await db.commit()


@router.post("/channels/{channel_id}/refresh", response_model=ChannelResponse)
async def refresh_channel(
    channel_id: str = Path(..., pattern="^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"),
    db: AsyncSession = Depends(get_db)
):
    """
    Check for new videos for a specific channel.

    Logic:
    1. Fetch current RSS feed
    2. Compare with last_video_id
    3. Add any new videos with status='inbox'
    4. Update last_checked and last_video_id
    """
    # Check if channel exists
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    channel = result.scalar_one_or_none()

    if not channel:
        raise NotFoundError("Channel", channel_id)

    # Fetch current RSS feed
    timeout = await get_http_timeout(db)
    try:
        videos_info = await fetch_videos(channel.rss_url, limit=50, timeout=timeout)
    except Exception as e:
        raise ExternalServiceError("YouTube", "fetch videos", str(e))

    # Add new videos and update channel
    new_videos_added = await process_new_videos(db, channel, videos_info)

    await db.commit()
    await db.refresh(channel)

    return await channel_to_response(db, channel)


@router.post("/channels/refresh-all", response_model=RefreshSummary)
async def refresh_all_channels(db: AsyncSession = Depends(get_db)):
    """
    Refresh all channels and return a summary.

    Uses parallel fetching with a semaphore to limit concurrent requests.

    Returns:
        Summary with number of channels refreshed, new videos found, and any errors
    """
    return await refresh_all_channels_service(db)