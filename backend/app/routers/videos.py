"""
Video management API router.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, delete
from sqlalchemy.orm import selectinload
from datetime import datetime
from typing import List, Optional

from ..database import get_db
from ..models.video import Video
from ..models.channel import Channel
from ..schemas.video import VideoResponse, VideoFromUrl, BulkVideoAction
from ..services.youtube_utils import extract_video_id, get_video_url, get_rss_url
from ..services.rss_parser import fetch_video_by_id, fetch_channel_info

router = APIRouter()


async def video_to_response(db: AsyncSession, video: Video) -> VideoResponse:
    """Convert a Video model to VideoResponse with channel name."""
    channel_name = None
    if video.channel:
        channel_name = video.channel.name
    
    return VideoResponse(
        id=video.id,
        youtube_video_id=video.youtube_video_id,
        channel_id=video.channel_id,
        channel_name=channel_name,
        title=video.title,
        description=video.description,
        thumbnail_url=video.thumbnail_url,
        video_url=video.video_url,
        published_at=video.published_at,
        status=video.status,
        saved_at=video.saved_at,
        discarded_at=video.discarded_at
    )


@router.get("/videos/inbox", response_model=List[VideoResponse])
async def list_inbox_videos(db: AsyncSession = Depends(get_db)):
    """
    List all videos with status='inbox'.
    """
    result = await db.execute(
        select(Video)
        .options(selectinload(Video.channel))
        .where(Video.status == 'inbox')
        .order_by(Video.published_at.desc())
    )
    videos = result.scalars().all()
    
    responses = []
    for video in videos:
        response = await video_to_response(db, video)
        responses.append(response)
    
    return responses


@router.get("/videos/saved", response_model=List[VideoResponse])
async def list_saved_videos(
    channel_id: Optional[str] = Query(None, description="Filter by channel ID"),
    sort_by: str = Query("published_at", description="Sort by 'published_at' or 'saved_at'"),
    order: str = Query("desc", description="Order 'asc' or 'desc'"),
    db: AsyncSession = Depends(get_db)
):
    """
    List saved videos with filtering and sorting.
    
    Query params:
        channel_id: Filter by channel (optional)
        sort_by: 'published_at' or 'saved_at'
        order: 'asc' or 'desc'
    """
    # Validate sort_by
    if sort_by not in ['published_at', 'saved_at']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="sort_by must be 'published_at' or 'saved_at'"
        )
    
    # Validate order
    if order not in ['asc', 'desc']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="order must be 'asc' or 'desc'"
        )
    
    # Build query
    query = (
        select(Video)
        .options(selectinload(Video.channel))
        .where(Video.status == 'saved')
    )
    
    # Apply channel filter if provided
    if channel_id:
        query = query.where(Video.channel_id == channel_id)
    
    # Apply sorting
    sort_column = Video.published_at if sort_by == 'published_at' else Video.saved_at
    if order == 'asc':
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())
    
    result = await db.execute(query)
    videos = result.scalars().all()
    
    responses = []
    for video in videos:
        response = await video_to_response(db, video)
        responses.append(response)
    
    return responses


@router.get("/videos/discarded", response_model=List[VideoResponse])
async def list_discarded_videos(
    days: int = Query(30, description="Number of days to look back for discarded videos"),
    db: AsyncSession = Depends(get_db)
):
    """
    List recently discarded videos (default: last 30 days).
    
    Query params:
        days: Number of days to look back (default: 30)
    """
    from datetime import timedelta
    
    # Calculate cutoff date
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    
    # Build query
    query = (
        select(Video)
        .options(selectinload(Video.channel))
        .where(Video.status == 'discarded')
        .where(Video.discarded_at >= cutoff_date)
        .order_by(Video.discarded_at.desc())
    )
    
    result = await db.execute(query)
    videos = result.scalars().all()
    
    responses = []
    for video in videos:
        response = await video_to_response(db, video)
        responses.append(response)
    
    return responses


@router.post("/videos/{video_id}/save", response_model=VideoResponse)
async def save_video(video_id: str, db: AsyncSession = Depends(get_db)):
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video with ID {video_id} not found"
        )
    
    # Update status and saved_at
    video.status = 'saved'
    video.saved_at = datetime.utcnow()
    video.discarded_at = None
    
    await db.commit()
    await db.refresh(video)
    
    return await video_to_response(db, video)


@router.post("/videos/{video_id}/discard", response_model=VideoResponse)
async def discard_video(video_id: str, db: AsyncSession = Depends(get_db)):
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video with ID {video_id} not found"
        )
    
    # Update status and discarded_at
    video.status = 'discarded'
    video.discarded_at = datetime.utcnow()
    video.saved_at = None
    
    await db.commit()
    await db.refresh(video)
    
    return await video_to_response(db, video)


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
    now = datetime.utcnow()
    for video in videos:
        video.status = 'saved'
        video.saved_at = now
        video.discarded_at = None
    
    await db.commit()
    
    # Build responses
    responses = []
    for video in videos:
        await db.refresh(video)
        response = await video_to_response(db, video)
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
    now = datetime.utcnow()
    for video in videos:
        video.status = 'discarded'
        video.discarded_at = now
        video.saved_at = None
    
    await db.commit()
    
    # Build responses
    responses = []
    for video in videos:
        await db.refresh(video)
        response = await video_to_response(db, video)
        responses.append(response)
    
    return responses


@router.post("/videos/from-url", response_model=VideoResponse)
async def add_video_from_url(video_data: VideoFromUrl, db: AsyncSession = Depends(get_db)):
    """
    Add a video from a YouTube URL.
    
    Logic:
    1. Extract video ID from URL
    2. Check if video already exists (return existing with 200 if so)
    3. Fetch video info from RSS/oEmbed
    4. Create video with status='saved' and saved_at=now (return 201)
    5. If video's channel exists, link it; otherwise channel_id=null
    """
    # Step 1: Extract video ID
    try:
        youtube_video_id = extract_video_id(video_data.url)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    
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
        existing_video.saved_at = datetime.utcnow()
        existing_video.discarded_at = None
        
        await db.commit()
        await db.refresh(existing_video)
        
        # Return updated video with 200 status
        from fastapi.responses import JSONResponse
        response_data = await video_to_response(db, existing_video)
        return JSONResponse(
            status_code=status.HTTP_200_OK,
            content=response_data.model_dump(mode='json')
        )
    
    # Step 3: Fetch video info
    try:
        video_info = await fetch_video_by_id(youtube_video_id)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch video info: {str(e)}"
        )
    
    # Step 4: Try to find or create the channel
    channel_id = None
    if video_info.channel_id:
        channel_result = await db.execute(
            select(Channel).where(Channel.youtube_channel_id == video_info.channel_id)
        )
        channel = channel_result.scalar_one_or_none()
        
        if not channel:
            # Create the channel if it doesn't exist so it shows up in filters
            try:
                channel_data = await fetch_channel_info(video_info.channel_id)
                channel = Channel(
                    youtube_channel_id=video_info.channel_id,
                    name=channel_data.name,
                    rss_url=get_rss_url(video_info.channel_id),
                    thumbnail_url=channel_data.thumbnail_url,
                    last_checked=datetime.utcnow()
                )
                db.add(channel)
                await db.flush() # Get the channel.id
            except Exception:
                # If channel creation fails, we still want to add the video
                # but it won't be linked to a channel record
                channel = None
        
        if channel:
            channel_id = channel.id
    
    # Step 5: Create video with status='saved'
    now = datetime.utcnow()
    video = Video(
        youtube_video_id=video_info.video_id,
        channel_id=channel_id,
        title=video_info.title,
        description=video_info.description,
        thumbnail_url=video_info.thumbnail_url,
        video_url=video_info.video_url,
        published_at=video_info.published_at,
        status='saved',
        saved_at=now
    )
    db.add(video)
    await db.commit()
    await db.refresh(video)
    
    # Load channel for response
    await db.refresh(video, ['channel'])
    
    # Return new video with 201 status
    from fastapi.responses import JSONResponse
    response_data = await video_to_response(db, video)
    return JSONResponse(
        status_code=status.HTTP_201_CREATED,
        content=response_data.model_dump(mode='json')
    )


@router.delete("/videos/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(video_id: str, db: AsyncSession = Depends(get_db)):
    """
    Delete a video.
    """
    # Check if video exists
    result = await db.execute(select(Video).where(Video.id == video_id))
    video = result.scalar_one_or_none()
    
    if not video:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Video with ID {video_id} not found"
        )
    
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
