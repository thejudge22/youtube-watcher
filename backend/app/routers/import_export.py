from datetime import datetime, timezone
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
    ExportData,
    ImportChannelsRequest,
    ImportVideosRequest,
    ImportUrlsRequest,
    ImportPlaylistRequest,
    ChannelImportResult,
    VideoImportResult,
)
from ..services.rss_parser import (
    fetch_channel_info,
    fetch_playlist_video_ids,
)
from ..services.youtube_utils import (
    extract_video_id,
    extract_playlist_id,
    get_rss_url,
    get_channel_url,
)
from ..services.settings_service import get_http_timeout
from ..schemas.mappers import map_video_to_export
from ..services.video_import_service import import_videos_by_id

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

    video_exports = [map_video_to_export(v) for v in videos]

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

    video_exports = [map_video_to_export(v) for v in videos]

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
            # Include embedded channel info for Issue #14
            # is_short defaults to False for imported videos (Issue #8)
            new_video = Video(
                youtube_video_id=video_data.youtube_video_id,
                channel_id=channel_id,
                channel_youtube_id=video_data.channel_youtube_id,  # Add embedded channel info
                channel_name=video_data.channel_name,  # Add embedded channel info
                channel_thumbnail_url=None,  # Can be fetched separately if needed
                title=video_data.title,
                description="",  # Not included in export
                thumbnail_url=thumbnail_url,
                video_url=video_data.video_url,
                published_at=video_data.published_at or datetime.now(timezone.utc),
                status="saved",
                saved_at=video_data.saved_at or datetime.now(timezone.utc),
                is_short=False,  # Issue #8: Default to False, can be detected later
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
    """Import videos from a list of YouTube URLs. Videos are added as saved.

    Blank lines are ignored (they only count toward the total); invalid URLs are
    reported as errors. Never subscribes to the videos' channels.
    """
    url_errors: list[str] = []
    video_ids: list[str] = []
    for raw_url in request.urls:
        url = raw_url.strip()
        if not url:
            continue
        try:
            video_ids.append(extract_video_id(url))
        except ValueError:
            url_errors.append(f"Invalid YouTube URL: {url}")

    timeout = await get_http_timeout(db)
    result = await import_videos_by_id(db, video_ids, timeout)

    return VideoImportResult(
        total=len(request.urls),
        imported=result.imported,
        skipped=result.skipped,
        errors=url_errors + result.errors,
    )


@router.post("/import/playlist", response_model=VideoImportResult)
async def import_playlist(
    request: ImportPlaylistRequest,
    db: AsyncSession = Depends(get_db),
):
    """Import videos from a YouTube playlist URL. Videos are added as saved.

    Only YouTube playlist URLs are accepted; the URL handed to yt-dlp is rebuilt
    from the playlist ID so it can never point at another host.
    """
    try:
        playlist_id = extract_playlist_id(request.url)
    except ValueError as e:
        return VideoImportResult(total=0, imported=0, skipped=0, errors=[str(e)])

    timeout = await get_http_timeout(db)
    try:
        video_ids = await fetch_playlist_video_ids(
            f"https://www.youtube.com/playlist?list={playlist_id}", timeout=timeout
        )
        logger.info(f"Found {len(video_ids)} videos in playlist")
    except ValueError as e:
        return VideoImportResult(total=0, imported=0, skipped=0, errors=[str(e)])

    return await import_videos_by_id(db, video_ids, timeout)
