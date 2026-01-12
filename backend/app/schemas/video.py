"""
Pydantic schemas for video API requests and responses.
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class VideoResponse(BaseModel):
    """Schema for video response."""
    id: str
    youtube_video_id: str
    channel_id: Optional[str]
    channel_name: Optional[str]
    title: str
    description: Optional[str]
    thumbnail_url: Optional[str]
    video_url: str
    published_at: datetime
    status: str
    saved_at: Optional[datetime]
    discarded_at: Optional[datetime]


class VideoFromUrl(BaseModel):
    """Schema for adding a video from URL."""
    url: str


class BulkVideoAction(BaseModel):
    """Schema for bulk video actions."""
    video_ids: List[str]
