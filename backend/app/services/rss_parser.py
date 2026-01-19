"""
RSS feed parser for YouTube channels.
"""

import httpx
import feedparser
import yt_dlp
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from .youtube_utils import get_rss_url, get_video_url, extract_channel_id, HTTP_HEADERS


class ChannelInfo(BaseModel):
    """Information about a YouTube channel."""
    channel_id: str
    name: str
    thumbnail_url: Optional[str] = None


class VideoInfo(BaseModel):
    """Information about a YouTube video."""
    video_id: str
    channel_id: str
    channel_name: str
    title: str
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    video_url: str
    published_at: datetime


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
)
async def fetch_channel_info(channel_id: str, timeout: float = 10.0) -> ChannelInfo:
    """
    Fetch channel information from the RSS feed.

    Retries up to 3 times with exponential backoff on HTTP errors.

    Args:
        channel_id: YouTube channel ID

    Returns:
        ChannelInfo object with channel name and thumbnail

    Raises:
        ValueError: If channel info cannot be extracted
    """
    rss_url = get_rss_url(channel_id)
    
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=HTTP_HEADERS) as client:
        response = await client.get(rss_url)
        response.raise_for_status()
        
        feed = feedparser.parse(response.content)
        
        if not feed.feed:
            raise ValueError(f"Could not parse RSS feed for channel: {channel_id}")
        
        # Extract channel name
        name = feed.feed.get('title', '')
        if not name:
            # Try author name as fallback
            author = feed.feed.get('author', '')
            name = author
        
        # Extract thumbnail from the first entry if available
        thumbnail_url = None
        if feed.entries:
            first_entry = feed.entries[0]
            # YouTube RSS includes channel thumbnail in media:thumbnail
            if 'media_thumbnail' in first_entry:
                thumbnails = first_entry.get('media_thumbnail', [])
                if thumbnails and isinstance(thumbnails, list) and len(thumbnails) > 0:
                    thumbnail_url = thumbnails[0].get('url')
            # Alternative: try to get from media_group
            elif 'media_group' in first_entry:
                media_group = first_entry.get('media_group', {})
                if 'media_thumbnail' in media_group:
                    thumbnails = media_group.get('media_thumbnail', [])
                    if thumbnails and isinstance(thumbnails, list) and len(thumbnails) > 0:
                        thumbnail_url = thumbnails[0].get('url')
        
        return ChannelInfo(
            channel_id=channel_id,
            name=name,
            thumbnail_url=thumbnail_url
        )


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
)
async def fetch_videos(rss_url: str, limit: int = 15, timeout: float = 10.0) -> List[VideoInfo]:
    """
    Fetch videos from a YouTube RSS feed.

    Retries up to 3 times with exponential backoff on HTTP errors.

    Args:
        rss_url: RSS feed URL
        limit: Maximum number of videos to return

    Returns:
        List of VideoInfo objects

    Raises:
        ValueError: If RSS feed cannot be parsed
    """
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=HTTP_HEADERS) as client:
        response = await client.get(rss_url)
        response.raise_for_status()
        
        feed = feedparser.parse(response.content)
        
        if not feed.entries:
            return []
        
        videos = []
        
        # Extract channel ID from the feed URL or from entries
        channel_id = None
        channel_name = ''
        
        # Try to get channel info from feed metadata
        if 'yt_channel_id' in feed.feed:
            channel_id = feed.feed['yt_channel_id']
        channel_name = feed.feed.get('title', '')
        
        # Limit the number of entries
        entries = feed.entries[:limit]
        
        for entry in entries:
            # Extract video ID
            video_id = None
            if 'yt_videoid' in entry:
                video_id = entry['yt_videoid']
            else:
                # Fallback: try to extract from link
                link = entry.get('link', '')
                if 'watch?v=' in link:
                    video_id = link.split('watch?v=')[-1].split('&')[0]
            
            if not video_id:
                continue
            
            # Extract channel ID from entry if not found in feed
            if not channel_id and 'yt_channelid' in entry:
                channel_id = entry['yt_channelid']
            
            # Extract title
            title = entry.get('title', '')
            
            # Extract description
            description = None
            if 'media_group' in entry:
                media_group = entry.get('media_group', {})
                description = media_group.get('media_description', '')
            elif 'description' in entry:
                description = entry.get('description', '')
            
            # Extract thumbnail
            thumbnail_url = None
            if 'media_thumbnail' in entry:
                thumbnails = entry.get('media_thumbnail', [])
                if thumbnails and isinstance(thumbnails, list) and len(thumbnails) > 0:
                    thumbnail_url = thumbnails[0].get('url')
            elif 'media_group' in entry:
                media_group = entry.get('media_group', {})
                if 'media_thumbnail' in media_group:
                    thumbnails = media_group.get('media_thumbnail', [])
                    if thumbnails and isinstance(thumbnails, list) and len(thumbnails) > 0:
                        thumbnail_url = thumbnails[0].get('url')
            
            # Fallback to default thumbnail URL if not found
            if not thumbnail_url and video_id:
                thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
            
            # Parse published date
            published_at = None
            if 'published_parsed' in entry and entry['published_parsed']:
                time_struct = entry['published_parsed']
                published_at = datetime(*time_struct[:6])
            elif 'updated_parsed' in entry and entry['updated_parsed']:
                time_struct = entry['updated_parsed']
                published_at = datetime(*time_struct[:6])
            else:
                # Use current time as fallback
                published_at = datetime.now(timezone.utc)
            
            # Build video URL
            video_url = get_video_url(video_id)
            
            videos.append(VideoInfo(
                video_id=video_id,
                channel_id=channel_id or '',
                channel_name=channel_name or '',
                title=title,
                description=description,
                thumbnail_url=thumbnail_url,
                video_url=video_url,
                published_at=published_at
            ))
        
        return videos


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((yt_dlp.utils.DownloadError,)),
)
async def fetch_video_by_id(video_id: str, timeout: float = 10.0) -> VideoInfo:
    """
    Fetch video information using yt-dlp.

    Retries up to 3 times with exponential backoff on download errors.

    Args:
        video_id: YouTube video ID

    Returns:
        VideoInfo object

    Raises:
        ValueError: If video info cannot be fetched
    """
    video_url = get_video_url(video_id)
    
    try:
        # Configure yt-dlp to extract metadata without downloading
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'skip_download': True,
            'extract_flat': False,  # We need full info for description/tags
        }
        
        # Extract video information
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
        
        # Extract fields from yt-dlp output
        title = info.get('title', '')
        channel_name = info.get('uploader', '')
        channel_id = info.get('channel_id', '')
        description = info.get('description', None)
        thumbnail_url = info.get('thumbnail', f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg")
        
        # Parse upload_date from YYYYMMDD string to datetime with UTC timezone
        upload_date_str = info.get('upload_date')
        if upload_date_str:
            # Parse YYYYMMDD format
            published_at = datetime.strptime(upload_date_str, '%Y%m%d').replace(tzinfo=timezone.utc)
        else:
            # Fallback to current time if upload_date is not available
            published_at = datetime.now(timezone.utc)
        
        return VideoInfo(
            video_id=video_id,
            channel_id=channel_id,
            channel_name=channel_name,
            title=title,
            description=description,
            thumbnail_url=thumbnail_url,
            video_url=video_url,
            published_at=published_at
        )
    except yt_dlp.utils.DownloadError as e:
        raise ValueError(f"Failed to fetch video info for {video_id}: {str(e)}")
