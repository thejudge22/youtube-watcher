"""
Response mappers for converting database models to response schemas.
"""

from ..models.video import Video
from ..services.youtube_utils import get_channel_url
from .import_export import VideoExport
from .video import VideoResponse


def map_video_to_response(video: Video) -> VideoResponse:
    """
    Convert a Video model to VideoResponse with channel name.

    Args:
        video: Video database model instance with optional channel relationship loaded

    Returns:
        VideoResponse schema instance
    """
    # Use embedded channel info, fall back to relationship if available
    channel_name = video.channel_name
    if not channel_name and video.channel:
        channel_name = video.channel.name

    channel_thumbnail = video.channel_thumbnail_url
    if not channel_thumbnail and video.channel:
        channel_thumbnail = video.channel.thumbnail_url

    return VideoResponse(
        id=video.id,
        youtube_video_id=video.youtube_video_id,
        channel_id=video.channel_id,
        channel_youtube_id=video.channel_youtube_id,
        channel_name=channel_name,
        channel_thumbnail_url=channel_thumbnail,
        title=video.title,
        description=video.description,
        thumbnail_url=video.thumbnail_url,
        video_url=video.video_url,
        published_at=video.published_at,
        status=video.status,
        saved_at=video.saved_at,
        discarded_at=video.discarded_at,
        is_short=video.is_short,  # Issue #8: Include Shorts status
        is_short_detected_at=video.is_short_detected_at  # Issue #55
    )


def map_video_to_export(video: Video) -> VideoExport:
    """
    Convert a saved Video to its export form.

    Channel info comes from the video's own copied fields, so videos from
    unsubscribed channels keep it; the subscription is only a fallback.
    """
    channel_youtube_id = video.channel_youtube_id or (video.channel.youtube_channel_id if video.channel else None)
    channel_name = video.channel_name or (video.channel.name if video.channel else None)
    if video.channel:
        channel_url = video.channel.youtube_url
    else:
        channel_url = get_channel_url(channel_youtube_id) if channel_youtube_id else None

    return VideoExport(
        youtube_video_id=video.youtube_video_id,
        title=video.title,
        video_url=video.video_url,
        channel_youtube_id=channel_youtube_id,
        channel_name=channel_name,
        channel_url=channel_url,
        saved_at=video.saved_at,
        published_at=video.published_at,
    )
