"""
RSS feed parser for YouTube channels.
"""

import httpx
import feedparser
from datetime import datetime, timezone
from typing import List, Optional
from pydantic import BaseModel

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


async def fetch_channel_info(channel_id: str) -> ChannelInfo:
    """
    Fetch channel information from the RSS feed.

    Args:
        channel_id: YouTube channel ID

    Returns:
        ChannelInfo object with channel name and thumbnail

    Raises:
        ValueError: If channel info cannot be extracted
    """
    rss_url = get_rss_url(channel_id)
    
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=HTTP_HEADERS) as client:
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


async def fetch_videos(rss_url: str, limit: int = 15) -> List[VideoInfo]:
    """
    Fetch videos from a YouTube RSS feed.

    Args:
        rss_url: RSS feed URL
        limit: Maximum number of videos to return

    Returns:
        List of VideoInfo objects

    Raises:
        ValueError: If RSS feed cannot be parsed
    """
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=HTTP_HEADERS) as client:
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


async def fetch_video_by_id(video_id: str) -> VideoInfo:
    """
    Fetch video information using the YouTube oEmbed endpoint.

    Args:
        video_id: YouTube video ID

    Returns:
        VideoInfo object

    Raises:
        ValueError: If video info cannot be fetched
    """
    video_url = get_video_url(video_id)
    
    # Use YouTube oEmbed endpoint to get video info
    oembed_url = f"https://www.youtube.com/oembed?url={video_url}&format=json"
    
    async with httpx.AsyncClient(timeout=10.0, follow_redirects=True, headers=HTTP_HEADERS) as client:
        response = await client.get(oembed_url)
        response.raise_for_status()
        
        data = response.json()
        
        title = data.get('title', '')
        author_name = data.get('author_name', '')
        author_url = data.get('author_url', '')
        
        # Extract channel ID from author_url if available
        channel_id = ''
        if author_url:
            try:
                channel_id = await extract_channel_id(author_url)
            except ValueError:
                # Fallback to empty if extraction fails
                pass
        
        # Use default thumbnail URL since oEmbed doesn't provide it
        thumbnail_url = f"https://i.ytimg.com/vi/{video_id}/hqdefault.jpg"
        
        # Use current time as published_at since oEmbed doesn't provide it
        published_at = datetime.now(timezone.utc)
        
        return VideoInfo(
            video_id=video_id,
            channel_id=channel_id,
            channel_name=author_name,
            title=title,
            description=None,  # Not available from oEmbed
            thumbnail_url=thumbnail_url,
            video_url=video_url,
            published_at=published_at
        )
