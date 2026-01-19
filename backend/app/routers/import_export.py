from datetime import datetime, timezone
import asyncio
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.channel import Channel
from ..models.video import Video
from ..schemas.import_export import (
    ChannelExport,
    VideoExport,
    ExportData,
    ImportChannelsRequest,
    ImportVideosRequest,
    ImportUrlsRequest,
    ChannelImportResult,
    VideoImportResult,
)
from ..services.rss_parser import (
    fetch_channel_info,
    fetch_video_by_id,
)
from ..services.youtube_utils import (
    extract_video_id,
    get_rss_url,
    get_channel_url,
)
from ..services.settings_service import get_http_timeout

router = APIRouter(prefix="/import-export", tags=["import-export"])

logger = logging.getLogger(__name__)


# ============ EXPORT ENDPOINTS ============

@router.get("/export/channels")
async def export_channels(db: AsyncSession = Depends(get_db)):
    """Export all channels as JSON."""
    result = await db.execute(select(Channel).order_by(Channel.name))
    channels = result.scalars().all()

    channel_exports = [
        ChannelExport(
            youtube_channel_id=c.youtube_channel_id,
            name=c.name,
            youtube_url=c.youtube_url,
        )
        for c in channels
    ]

    export_data = ExportData(
        version="1.0",
        exported_at=datetime.now(timezone.utc),
        channels=channel_exports,
        saved_videos=[],
    )

    return JSONResponse(
        content=export_data.model_dump(mode="json"),
        headers={
            "Content-Disposition": f'attachment; filename="youtube-watcher-channels-{datetime.now().strftime("%Y%m%d")}.json"'
        },
    )


@router.get("/export/saved-videos")
async def export_saved_videos(db: AsyncSession = Depends(get_db)):
    """Export all saved videos as JSON."""
    result = await db.execute(
        select(Video)
        .options(selectinload(Video.channel))
        .where(Video.status == "saved")
        .order_by(Video.saved_at.desc())
    )
    videos = result.scalars().all()

    video_exports = [
        VideoExport(
            youtube_video_id=v.youtube_video_id,
            title=v.title,
            video_url=v.video_url,
            channel_youtube_id=v.channel.youtube_channel_id if v.channel else None,
            channel_name=v.channel.name if v.channel else None,
            channel_url=v.channel.youtube_url if v.channel else None,
            saved_at=v.saved_at,
            published_at=v.published_at,
        )
        for v in videos
    ]

    export_data = ExportData(
        version="1.0",
        exported_at=datetime.now(timezone.utc),
        channels=[],
        saved_videos=video_exports,
    )

    return JSONResponse(
        content=export_data.model_dump(mode="json"),
        headers={
            "Content-Disposition": f'attachment; filename="youtube-watcher-saved-videos-{datetime.now().strftime("%Y%m%d")}.json"'
        },
    )


@router.get("/export/all")
async def export_all(db: AsyncSession = Depends(get_db)):
    """Export all channels and saved videos as JSON."""
    # Fetch channels
    channels_result = await db.execute(select(Channel).order_by(Channel.name))
    channels = channels_result.scalars().all()

    channel_exports = [
        ChannelExport(
            youtube_channel_id=c.youtube_channel_id,
            name=c.name,
            youtube_url=c.youtube_url,
        )
        for c in channels
    ]

    # Fetch saved videos
    videos_result = await db.execute(
        select(Video)
        .options(selectinload(Video.channel))
        .where(Video.status == "saved")
        .order_by(Video.saved_at.desc())
    )
    videos = videos_result.scalars().all()

    video_exports = [
        VideoExport(
            youtube_video_id=v.youtube_video_id,
            title=v.title,
            video_url=v.video_url,
            channel_youtube_id=v.channel.youtube_channel_id if v.channel else None,
            channel_name=v.channel.name if v.channel else None,
            channel_url=v.channel.youtube_url if v.channel else None,
            saved_at=v.saved_at,
            published_at=v.published_at,
        )
        for v in videos
    ]

    export_data = ExportData(
        version="1.0",
        exported_at=datetime.now(timezone.utc),
        channels=channel_exports,
        saved_videos=video_exports,
    )

    return JSONResponse(
        content=export_data.model_dump(mode="json"),
        headers={
            "Content-Disposition": f'attachment; filename="youtube-watcher-export-{datetime.now().strftime("%Y%m%d")}.json"'
        },
    )


# ============ IMPORT ENDPOINTS ============

@router.post("/import/channels", response_model=ChannelImportResult)
async def import_channels(
    request: ImportChannelsRequest,
    db: AsyncSession = Depends(get_db),
):
    """Import channels from JSON. Skips existing channels."""
    total = len(request.channels)
    imported = 0
    skipped = 0
    errors: list[str] = []

    for channel_data in request.channels:
        try:
            # Check if channel already exists
            existing = await db.execute(
                select(Channel).where(
                    Channel.youtube_channel_id == channel_data.youtube_channel_id
                )
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue

            # Fetch full channel info from YouTube
            channel_id = channel_data.youtube_channel_id
            timeout = await get_http_timeout(db)
            channel_info = await fetch_channel_info(channel_id, timeout=timeout)
            if not channel_info:
                errors.append(f"Could not fetch info for channel: {channel_data.name}")
                continue

            # Create new channel
            new_channel = Channel(
                youtube_channel_id=channel_id,
                name=channel_info.name,
                rss_url=get_rss_url(channel_id),
                youtube_url=channel_data.youtube_url,
                thumbnail_url=channel_info.thumbnail_url,
                last_checked=datetime.now(timezone.utc),
            )
            db.add(new_channel)
            await db.flush()
            imported += 1

        except Exception as e:
            errors.append(f"Error importing {channel_data.name}: {str(e)}")

    await db.commit()

    return ChannelImportResult(
        total=total,
        imported=imported,
        skipped=skipped,
        errors=errors,
    )


@router.post("/import/videos", response_model=VideoImportResult)
async def import_videos(
    request: ImportVideosRequest,
    db: AsyncSession = Depends(get_db),
):
    """Import saved videos from JSON. Skips existing videos."""
    total = len(request.videos)
    imported = 0
    skipped = 0
    errors: list[str] = []

    for video_data in request.videos:
        try:
            # Check if video already exists
            existing = await db.execute(
                select(Video).where(
                    Video.youtube_video_id == video_data.youtube_video_id
                )
            )
            existing_video = existing.scalar_one_or_none()

            if existing_video:
                # If video exists but not saved, mark it as saved
                if existing_video.status != "saved":
                    existing_video.status = "saved"
                    existing_video.saved_at = video_data.saved_at or datetime.now(timezone.utc)
                    imported += 1
                else:
                    skipped += 1
                continue

            # Find or create channel association using export data
            channel_id = None
            if video_data.channel_youtube_id:
                channel_result = await db.execute(
                    select(Channel).where(
                        Channel.youtube_channel_id == video_data.channel_youtube_id
                    )
                )
                channel = channel_result.scalar_one_or_none()

                if not channel:
                    # Channel doesn't exist, create it by fetching from YouTube
                    try:
                        # Fetch full channel info from YouTube
                        timeout = await get_http_timeout(db)
                        channel_info = await fetch_channel_info(video_data.channel_youtube_id, timeout=timeout)
                        if channel_info:
                            # Use channel_url from export if available, otherwise generate it
                            channel_url = video_data.channel_url or get_channel_url(video_data.channel_youtube_id)

                            channel = Channel(
                                youtube_channel_id=video_data.channel_youtube_id,
                                name=channel_info.name,
                                rss_url=get_rss_url(video_data.channel_youtube_id),
                                youtube_url=channel_url,
                                thumbnail_url=channel_info.thumbnail_url,
                                last_checked=datetime.now(timezone.utc),
                            )
                            db.add(channel)
                            await db.flush()
                    except Exception as e:
                        # If channel creation fails, continue without channel association
                        logger.warning(
                            f"Failed to create channel for import (channel_id={video_data.channel_youtube_id}): {str(e)}"
                        )

                if channel:
                    channel_id = channel.id

            # Use data from export (avoids unnecessary API calls)
            # Generate thumbnail URL from video ID
            thumbnail_url = f"https://i.ytimg.com/vi/{video_data.youtube_video_id}/hqdefault.jpg"

            # Create new video as saved using export data
            new_video = Video(
                youtube_video_id=video_data.youtube_video_id,
                channel_id=channel_id,
                title=video_data.title,
                description="",  # Not included in export
                thumbnail_url=thumbnail_url,
                video_url=video_data.video_url,
                published_at=video_data.published_at or datetime.now(timezone.utc),
                status="saved",
                saved_at=video_data.saved_at or datetime.now(timezone.utc),
            )
            db.add(new_video)
            await db.flush()
            imported += 1

        except Exception as e:
            errors.append(f"Error importing video {video_data.youtube_video_id}: {str(e)}")

    await db.commit()

    return VideoImportResult(
        total=total,
        imported=imported,
        skipped=skipped,
        errors=errors,
    )


@router.post("/import/video-urls", response_model=VideoImportResult)
async def import_video_urls(
    request: ImportUrlsRequest,
    db: AsyncSession = Depends(get_db),
):
    """Import videos from a list of YouTube URLs. Videos are added as saved."""
    total = len(request.urls)

    # Get timeout once for all requests
    timeout = await get_http_timeout(db)

    # Helper function to fetch video info with error handling
    async def fetch_video_info(video_id: str):
        try:
            return await fetch_video_by_id(video_id, timeout=timeout)
        except Exception as e:
            logger.warning(f"Failed to fetch video info for video_id={video_id}: {str(e)}")
            return None

    # Result container for each URL processing
    class UrlProcessResult:
        def __init__(self, imported: bool = False, skipped: bool = False, error: str = None):
            self.imported = imported
            self.skipped = skipped
            self.error = error

    # Process URLs in parallel batches to avoid overwhelming the API
    batch_size = 10
    semaphore = asyncio.Semaphore(batch_size)

    async def process_url(url: str) -> UrlProcessResult:
        """Process a single URL and return the result without shared state mutation."""
        url = url.strip()
        if not url:
            return UrlProcessResult()

        async with semaphore:
            try:
                # Extract video ID from URL
                video_id = extract_video_id(url)
                if not video_id:
                    return UrlProcessResult(error=f"Invalid YouTube URL: {url}")

                # Check if video already exists
                existing = await db.execute(
                    select(Video).where(Video.youtube_video_id == video_id)
                )
                existing_video = existing.scalar_one_or_none()

                if existing_video:
                    if existing_video.status != "saved":
                        existing_video.status = "saved"
                        existing_video.saved_at = datetime.now(timezone.utc)
                        return UrlProcessResult(imported=True)
                    else:
                        return UrlProcessResult(skipped=True)

                # Fetch video info from YouTube
                video_info = await fetch_video_info(video_id)
                if not video_info:
                    return UrlProcessResult(error=f"Could not fetch video: {url}")

                # Find or create channel association
                channel_id = None
                if video_info.channel_id:
                    channel_result = await db.execute(
                        select(Channel).where(
                            Channel.youtube_channel_id == video_info.channel_id
                        )
                    )
                    channel = channel_result.scalar_one_or_none()

                    if not channel:
                        # Channel doesn't exist, create it
                        try:
                            channel_info = await fetch_channel_info(video_info.channel_id, timeout=timeout)
                            if channel_info:
                                channel = Channel(
                                    youtube_channel_id=video_info.channel_id,
                                    name=channel_info.name,
                                    rss_url=get_rss_url(video_info.channel_id),
                                    youtube_url=get_channel_url(video_info.channel_id),
                                    thumbnail_url=channel_info.thumbnail_url,
                                    last_checked=datetime.now(timezone.utc),
                                )
                                db.add(channel)
                                await db.flush()
                        except Exception as e:
                            # If channel creation fails, continue without channel association
                            logger.warning(
                                f"Failed to create channel during URL import (channel_id={video_info.channel_id}): {str(e)}"
                            )

                    if channel:
                        channel_id = channel.id

                # Create new video as saved
                new_video = Video(
                    youtube_video_id=video_info.video_id,
                    channel_id=channel_id,
                    title=video_info.title,
                    description=video_info.description or "",
                    thumbnail_url=video_info.thumbnail_url,
                    video_url=video_info.video_url,
                    published_at=video_info.published_at,
                    status="saved",
                    saved_at=datetime.now(timezone.utc),
                )
                db.add(new_video)
                await db.flush()
                return UrlProcessResult(imported=True)

            except Exception as e:
                return UrlProcessResult(error=f"Error importing {url}: {str(e)}")

    # Process all URLs in parallel (with semaphore limiting concurrency)
    results = await asyncio.gather(*[process_url(url) for url in request.urls])

    # Aggregate results after all processing is complete
    imported = sum(1 for r in results if r.imported)
    skipped = sum(1 for r in results if r.skipped)
    errors = [r.error for r in results if r.error]

    await db.commit()

    return VideoImportResult(
        total=total,
        imported=imported,
        skipped=skipped,
        errors=errors,
    )
