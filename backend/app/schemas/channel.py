"""
Pydantic schemas for channel API requests and responses.
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ChannelCreate(BaseModel):
    """Schema for creating a new channel."""
    url: str


class ChannelResponse(BaseModel):
    """Schema for channel response."""
    id: str
    youtube_channel_id: str
    name: str
    youtube_url: str
    thumbnail_url: Optional[str]
    last_checked: Optional[datetime]
    video_count: int  # Count of inbox + saved videos


class RefreshSummary(BaseModel):
    """Schema for refresh operation summary."""
    channels_refreshed: int
    new_videos_found: int
    errors: list[str] = []
