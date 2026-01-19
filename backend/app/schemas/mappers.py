"""
Response mappers for converting database models to response schemas.
"""

from ..models.video import Video
from .video import VideoResponse


def map_video_to_response(video: Video) -> VideoResponse:
    """
    Convert a Video model to VideoResponse with channel name.
    
    Args:
        video: Video database model instance with optional channel relationship loaded
        
    Returns:
        VideoResponse schema instance
    """
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
