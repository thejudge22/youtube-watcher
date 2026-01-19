"""
Channel management API router.
"""

import asyncio
from fastapi import APIRouter, Depends, HTTPException, status, Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from datetime import datetime, timezone
from typing import List, Dict

from ..database import get_db
from ..models.channel import Channel
from ..models.video import Video
from ..schemas.channel import ChannelCreate, ChannelResponse, RefreshSummary
from ..services.youtube_utils import extract_channel_id, get_rss_url, get_channel_url
from ..services.rss_parser import fetch_channel_info, fetch_videos, VideoInfo
from ..services.settings_service import get_http_timeout
from ..exceptions import NotFoundError, AlreadyExistsError, ValidationError, ExternalServiceError

router = APIRouter()


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
    result = await db.execute(select(Channel).order_by(Channel.name))
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
    for video_info in videos_info:
        video = Video(
            youtube_video_id=video_info.video_id,
            channel_id=channel.id,
            title=video_info.title,
            description=video_info.description,
            thumbnail_url=video_info.thumbnail_url,
            video_url=video_info.video_url,
            published_at=video_info.published_at,
            status='inbox'
        )
        db.add(video)
    
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
    new_videos_added = await _process_new_videos(db, channel, videos_info)

    await db.commit()
    await db.refresh(channel)

    return await channel_to_response(db, channel)


async def _process_new_videos(
    db: AsyncSession, channel: Channel, videos_info: List[VideoInfo]
) -> int:
    """
    Process new videos for a channel. Updates channel's last_checked and last_video_id.

    Returns the number of new videos added.
    """
    new_videos_added = 0
    new_last_video_id = channel.last_video_id

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
            title=video_info.title,
            description=video_info.description,
            thumbnail_url=video_info.thumbnail_url,
            video_url=video_info.video_url,
            published_at=video_info.published_at,
            status='inbox'
        )
        db.add(video)
        new_videos_added += 1

        # Update last_video_id if this is the newest video
        if new_last_video_id is None or new_videos_added == 1:
            new_last_video_id = video_info.video_id

    # Update last_checked and last_video_id
    channel.last_checked = datetime.now(timezone.utc)
    if new_last_video_id:
        channel.last_video_id = new_last_video_id

    return new_videos_added


async def _fetch_channel_videos(channel: Channel, timeout: float) -> tuple[Channel, List[VideoInfo] | None, str | None]:
    """
    Fetch videos for a channel. Returns (channel, videos_info, error).
    Error is None on success.
    """
    try:
        videos_info = await fetch_videos(channel.rss_url, limit=50, timeout=timeout)
        return (channel, videos_info, None)
    except Exception as e:
        return (channel, None, str(e))


@router.post("/channels/refresh-all", response_model=RefreshSummary)
async def refresh_all_channels(db: AsyncSession = Depends(get_db)):
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
    semaphore = asyncio.Semaphore(5)  # Limit to 5 concurrent requests

    async def fetch_with_semaphore(channel: Channel):
        async with semaphore:
            return await _fetch_channel_videos(channel, timeout)

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
            new_videos_added = await _process_new_videos(db, channel, videos_info)
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
