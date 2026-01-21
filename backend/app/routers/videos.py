"""
Video management API router.
"""

from datetime import datetime, timedelta, timezone
from typing import List, Optional
import logging

from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.video import Video
from ..models.channel import Channel
from ..schemas.video import VideoResponse, VideoFromUrl, BulkVideoAction, ChannelFilterOption, PaginatedVideosResponse
from pydantic import BaseModel
from ..schemas.mappers import map_video_to_response
from ..services.youtube_utils import extract_video_id, get_video_url, get_rss_url, get_channel_url
from ..services.rss_parser import fetch_video_by_id, fetch_channel_info
from ..services.settings_service import get_http_timeout
from ..services.video_service import VideoService
from ..exceptions import NotFoundError, ValidationError, ExternalServiceError

router = APIRouter()

logger = logging.getLogger(__name__)


@router.get("/videos/inbox", response_model=List[VideoResponse])
async def list_inbox_videos(
    limit: int = Query(100, ge=1, le=500, description="Maximum number of videos to return"),
    offset: int = Query(0, ge=0, description="Number of videos to skip"),
    channel_id: Optional[str] = Query(None, description="Filter by channel ID"),
    is_short: Optional[bool] = Query(None, description="Filter by Shorts status (True=Shorts only, False=regular only, None=all)"),
    db: AsyncSession = Depends(get_db)
):
    """
    List all videos with status='inbox' with pagination.

    Query params:
        limit: Maximum number of videos to return (default: 100, max: 500)
        offset: Number of videos to skip (default: 0)
        channel_id: Filter by channel (optional)
        is_short: Filter by Shorts status (optional, None=all, True=shorts only, False=regular only) - Issue #8
    """
    # Use VideoService to fetch inbox videos
    videos = await VideoService.get_videos(
        db=db,
        status='inbox',
        limit=limit,
        offset=offset,
        channel_id=channel_id,
        is_short=is_short,  # Issue #8: Pass Shorts filter
        sort_by='published_at',
        order='desc'
    )

    return [
        VideoResponse(
            id=video.id,
            youtube_video_id=video.youtube_video_id,
            channel_id=video.channel_id,
            channel_youtube_id=video.channel_youtube_id,
            channel_name=video.channel_name or (video.channel.name if video.channel else None),
            channel_thumbnail_url=video.channel_thumbnail_url or (video.channel.thumbnail_url if video.channel else None),
            title=video.title,
            description=video.description,
            thumbnail_url=video.thumbnail_url,
            video_url=video.video_url,
            published_at=video.published_at,
            status=video.status,
            saved_at=video.saved_at,
            discarded_at=video.discarded_at,
            is_short=video.is_short  # Issue #8: Include Shorts status
        )
        for video in videos
    ]


@router.get("/videos/saved", response_model=PaginatedVideosResponse)
async def list_saved_videos(
    channel_youtube_id: Optional[str] = Query(None, description="Filter by channel YouTube ID"),
    channel_id: Optional[str] = Query(None, description="Filter by channel ID (deprecated)"),
    sort_by: str = Query("published_at", description="Sort by 'published_at' or 'saved_at'"),
    order: str = Query("desc", description="Order 'asc' or 'desc'"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of videos to return"),
    offset: int = Query(0, ge=0, description="Number of videos to skip"),
    db: AsyncSession = Depends(get_db)
):
    """
    List saved videos with filtering, sorting, and pagination.

    Query params:
        channel_youtube_id: Filter by channel YouTube ID (uses embedded channel info)
        channel_id: Filter by channel ID (deprecated, use channel_youtube_id)
        sort_by: 'published_at' or 'saved_at'
        order: 'asc' or 'desc'
        limit: Maximum number of videos to return (default: 100, max: 500)
        offset: Number of videos to skip (default: 0)
    """
    # Support both new and deprecated filter params
    filter_channel_youtube_id = channel_youtube_id

    # If old param is provided, look up the youtube_channel_id
    if not filter_channel_youtube_id and channel_id:
        channel_result = await db.execute(
            select(Channel.youtube_channel_id).where(Channel.id == channel_id)
        )
        channel_record = channel_result.scalar_one_or_none()
        if channel_record:
            filter_channel_youtube_id = channel_record

    # Get total count for pagination
    count_query = select(func.count(Video.id)).where(Video.status == 'saved')
    if filter_channel_youtube_id:
        count_query = count_query.where(Video.channel_youtube_id == filter_channel_youtube_id)
    count_result = await db.execute(count_query)
    total = count_result.scalar_one()

    # Use VideoService to fetch saved videos
    # Validation is handled within VideoService.get_videos
    videos = await VideoService.get_videos(
        db=db,
        status='saved',
        limit=limit,
        offset=offset,
        channel_youtube_id=filter_channel_youtube_id,
        sort_by=sort_by,
        order=order
    )

    video_responses = [
        VideoResponse(
            id=video.id,
            youtube_video_id=video.youtube_video_id,
            channel_id=video.channel_id,
            channel_youtube_id=video.channel_youtube_id,
            channel_name=video.channel_name or (video.channel.name if video.channel else None),
            channel_thumbnail_url=video.channel_thumbnail_url or (video.channel.thumbnail_url if video.channel else None),
            title=video.title,
            description=video.description,
            thumbnail_url=video.thumbnail_url,
            video_url=video.video_url,
            published_at=video.published_at,
            status=video.status,
            saved_at=video.saved_at,
            discarded_at=video.discarded_at,
            is_short=video.is_short  # Issue #8: Include Shorts status
        )
        for video in videos
    ]

    return PaginatedVideosResponse(
        videos=video_responses,
        total=total,
        limit=limit,
        offset=offset,
        has_more=(offset + len(video_responses)) < total
    )


@router.get("/videos/saved/channels", response_model=List[ChannelFilterOption])
async def list_saved_video_channels(
    db: AsyncSession = Depends(get_db)
):
    """
    List all unique channels that have saved videos.

    Returns channels with video counts, sorted by name.
    Used for the channel filter on the Saved Videos page.
    """
    # Group only by channel_youtube_id to avoid duplicates when
    # channel_thumbnail_url differs (some null, some with value)
    # Use MAX() to get a non-null thumbnail if available
    result = await db.execute(
        select(
            Video.channel_youtube_id,
            Video.channel_name,
            func.max(Video.channel_thumbnail_url).label('channel_thumbnail_url'),
            func.count(Video.id).label('video_count')
        )
        .where(Video.status == 'saved')
        .where(Video.channel_youtube_id.isnot(None))
        .group_by(Video.channel_youtube_id, Video.channel_name)
        .order_by(Video.channel_name)
    )

    return [
        ChannelFilterOption(
            channel_youtube_id=row.channel_youtube_id,
            channel_name=row.channel_name or "Unknown Channel",
            channel_thumbnail_url=row.channel_thumbnail_url,
            video_count=row.video_count
        )
        for row in result.all()
    ]


@router.get("/videos/discarded", response_model=List[VideoResponse])
async def list_discarded_videos(
    days: int = Query(30, ge=1, le=365, description="Number of days to look back for discarded videos"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of videos to return"),
    offset: int = Query(0, ge=0, description="Number of videos to skip"),
    db: AsyncSession = Depends(get_db)
):
    """
    List recently discarded videos with pagination.

    Query params:
        days: Number of days to look back (default: 30, max: 365)
        limit: Maximum number of videos to return (default: 100, max: 500)
        offset: Number of videos to skip (default: 0)
    """
    # Calculate cutoff date
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)

    # Use VideoService to fetch discarded videos
    videos = await VideoService.get_discarded_videos(
        db=db,
        cutoff_date=cutoff_date,
        limit=limit,
        offset=offset
    )

    return [
        VideoResponse(
            id=video.id,
            youtube_video_id=video.youtube_video_id,
            channel_id=video.channel_id,
            channel_youtube_id=video.channel_youtube_id,
            channel_name=video.channel_name or (video.channel.name if video.channel else None),
            channel_thumbnail_url=video.channel_thumbnail_url or (video.channel.thumbnail_url if video.channel else None),
            title=video.title,
            description=video.description,
            thumbnail_url=video.thumbnail_url,
            video_url=video.video_url,
            published_at=video.published_at,
            status=video.status,
            saved_at=video.saved_at,
            discarded_at=video.discarded_at,
            is_short=video.is_short  # Issue #8: Include Shorts status
        )
        for video in videos
    ]


@router.post("/videos/{video_id}/save", response_model=VideoResponse)
async def save_video(
    video_id: str = Path(..., pattern="^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"),
    db: AsyncSession = Depends(get_db)
):
    """
    Update video status to 'saved' and set saved_at to now.
    """
    # Check if video exists
    result = await db.execute(
        select(Video)
        .options(selectinload(Video.channel))
        .where(Video.id == video_id)
    )
    video = result.scalar_one_or_none()

    if not video:
        raise NotFoundError("Video", video_id)

    # Update status and saved_at
    video.status = 'saved'
    video.saved_at = datetime.now(timezone.utc)
    video.discarded_at = None

    await db.commit()
    await db.refresh(video)

    return map_video_to_response(video)


@router.post("/videos/{video_id}/discard", response_model=VideoResponse)
async def discard_video(
    video_id: str = Path(..., pattern="^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"),
    db: AsyncSession = Depends(get_db)
):
    """
    Update video status to 'discarded' and set discarded_at to now.
    """
    # Check if video exists
    result = await db.execute(
        select(Video)
        .options(selectinload(Video.channel))
        .where(Video.id == video_id)
    )
    video = result.scalar_one_or_none()

    if not video:
        raise NotFoundError("Video", video_id)

    # Update status and discarded_at
    video.status = 'discarded'
    video.discarded_at = datetime.now(timezone.utc)
    video.saved_at = None
    
    await db.commit()
    await db.refresh(video)
    
    return map_video_to_response(video)


@router.post("/videos/bulk-save", response_model=List[VideoResponse])
async def bulk_save_videos(action: BulkVideoAction, db: AsyncSession = Depends(get_db)):
    """
    Bulk save multiple videos.
    """
    if not action.video_ids:
        return []
    
    # Fetch all videos
    result = await db.execute(
        select(Video)
        .options(selectinload(Video.channel))
        .where(Video.id.in_(action.video_ids))
    )
    videos = result.scalars().all()
    
    # Update each video
    now = datetime.now(timezone.utc)
    for video in videos:
        video.status = 'saved'
        video.saved_at = now
        video.discarded_at = None
    
    await db.commit()
    
    # Build responses
    responses = []
    for video in videos:
        await db.refresh(video)
        response = map_video_to_response(video)
        responses.append(response)
    
    return responses


@router.post("/videos/bulk-discard", response_model=List[VideoResponse])
async def bulk_discard_videos(action: BulkVideoAction, db: AsyncSession = Depends(get_db)):
    """
    Bulk discard multiple videos.
    """
    if not action.video_ids:
        return []
    
    # Fetch all videos
    result = await db.execute(
        select(Video)
        .options(selectinload(Video.channel))
        .where(Video.id.in_(action.video_ids))
    )
    videos = result.scalars().all()
    
    # Update each video
    now = datetime.now(timezone.utc)
    for video in videos:
        video.status = 'discarded'
        video.discarded_at = now
        video.saved_at = None
    
    await db.commit()
    
    # Build responses
    responses = []
    for video in videos:
        await db.refresh(video)
        response = map_video_to_response(video)
        responses.append(response)
    
    return responses


@router.post("/videos/from-url", response_model=VideoResponse)
async def add_video_from_url(video_data: VideoFromUrl, db: AsyncSession = Depends(get_db)):
    """
    Add a video from a YouTube URL.

    Logic:
    1. Extract video ID from URL
    2. Check if video already exists (update to saved with 200 if so)
    3. Fetch video info from RSS/oEmbed
    4. Check if channel exists in channels table (don't create if not)
    5. Create video with embedded channel info (does NOT create channel record)

    Issue #8: Includes automatic Shorts detection from video info.
    """
    # Step 1: Extract video ID
    try:
        youtube_video_id = extract_video_id(video_data.url)
    except ValueError as e:
        raise ValidationError(str(e), field="url")

    # Step 2: Check if video already exists
    existing = await db.execute(
        select(Video)
        .options(selectinload(Video.channel))
        .where(Video.youtube_video_id == youtube_video_id)
    )
    existing_video = existing.scalar_one_or_none()

    if existing_video:
        # If video exists, update it to 'saved' status regardless of current status
        # This allows re-saving previously discarded videos
        existing_video.status = 'saved'
        existing_video.saved_at = datetime.now(timezone.utc)
        existing_video.discarded_at = None

        await db.commit()
        await db.refresh(existing_video)

        # Return updated video with 200 status
        response_data = map_video_to_response(existing_video)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data.model_dump(mode='json')
        )

    # Step 3: Fetch video info
    timeout = await get_http_timeout(db)
    try:
        video_info = await fetch_video_by_id(youtube_video_id, timeout=timeout)
    except Exception as e:
        raise ExternalServiceError("YouTube", "fetch video info", str(e))

    # Step 4: Check if channel exists in channels table (don't create if not)
    channel_id = None
    if video_info.channel_id:
        channel_result = await db.execute(
            select(Channel).where(Channel.youtube_channel_id == video_info.channel_id)
        )
        channel = channel_result.scalar_one_or_none()
        if channel:
            channel_id = channel.id

    # Step 5: Create video with embedded channel info
    now = datetime.now(timezone.utc)
    video = Video(
        youtube_video_id=video_info.video_id,
        channel_id=channel_id,  # May be None if channel not tracked
        channel_youtube_id=video_info.channel_id,
        channel_name=video_info.channel_name,
        channel_thumbnail_url=None,  # Can fetch separately if needed
        title=video_info.title,
        description=video_info.description,
        thumbnail_url=video_info.thumbnail_url,
        video_url=video_info.video_url,
        published_at=video_info.published_at,
        status='saved',
        saved_at=now,
        is_short=video_info.is_short  # Issue #8: Include Shorts detection
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)

    # Load channel for response if it exists
    if channel_id:
        await db.refresh(video, ['channel'])

    response_data = map_video_to_response(video)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=response_data.model_dump(mode='json')
    )


@router.delete("/videos/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(
    video_id: str = Path(..., pattern="^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a video.
    """
    # Check if video exists
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()

    if not video:
        raise NotFoundError("Video", video_id)
    
    # Delete the video
    await db.execute(delete(Video).where(Video.id == video_id))
    await db.commit()


@router.delete("/videos/discarded/purge-all", status_code=status.HTTP_200_OK)
async def purge_all_discarded_videos(db: AsyncSession = Depends(get_db)):
    """
    Permanently delete all discarded videos.

    Returns:
        dict: Summary of deletion including count of deleted videos
    """
    # Count videos to be deleted
    count_result = await db.execute(
        select(func.count(Video.id)).where(Video.status == 'discarded')
    )
    count = count_result.scalar_one()

    # Delete all discarded videos
    await db.execute(delete(Video).where(Video.status == 'discarded'))
    await db.commit()

    return {"deleted_count": count, "message": f"Successfully deleted {count} discarded video(s)"}


# Issue #8: YouTube Shorts Detection Endpoints

class BatchDetectRequest(BaseModel):
    """Request schema for batch Shorts detection."""
    video_ids: Optional[List[str]] = None


@router.post("/videos/{video_id}/detect-short", response_model=VideoResponse)
async def detect_video_short(
    video_id: str = Path(..., pattern="^[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}$"),
    db: AsyncSession = Depends(get_db)
):
    """
    Detect if a video is a YouTube Short and update its status.

    Fetches video info via yt-dlp and checks if URL contains /shorts/.

    Issue #8: YouTube Shorts Separation
    """
    # Get video
    result = await db.execute(
        select(Video)
        .options(selectinload(Video.channel))
        .where(Video.id == video_id)
    )
    video = result.scalar_one_or_none()

    if not video:
        raise NotFoundError("Video", video_id)

    # Fetch video info and detect if it's a Short via URL
    timeout = await get_http_timeout(db)
    try:
        video_info = await fetch_video_by_id(video.youtube_video_id, timeout=timeout)
        video.is_short = video_info.is_short
        await db.commit()
        await db.refresh(video)
    except Exception as e:
        logger.warning(f"Could not detect Short status for {video.youtube_video_id}: {e}")

    return map_video_to_response(video)


@router.post("/videos/detect-shorts-batch")
async def detect_shorts_batch(
    request: BatchDetectRequest = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Detect Shorts status for multiple videos or all inbox videos.

    If video_ids is provided, detects for those specific videos.
    Otherwise, detects for all inbox videos.
    Uses URL-based detection via yt-dlp.

    Issue #8: YouTube Shorts Separation

    Returns:
        dict: Summary with total_checked and updated_count
    """
    timeout = await get_http_timeout(db)

    if request and request.video_ids:
        # Detect for specific videos
        result = await db.execute(
            select(Video).where(Video.id.in_(request.video_ids))
        )
    else:
        # Detect for all inbox videos
        result = await db.execute(
            select(Video).where(Video.status == 'inbox')
        )

    videos = result.scalars().all()
    updated_count = 0

    for video in videos:
        try:
            video_info = await fetch_video_by_id(video.youtube_video_id, timeout=timeout)
            if video.is_short != video_info.is_short:
                video.is_short = video_info.is_short
                updated_count += 1
        except Exception as e:
            logger.warning(f"Could not detect Short status for {video.youtube_video_id}: {e}")

    await db.commit()

    return {
        "total_checked": len(videos),
        "updated_count": updated_count
    }
