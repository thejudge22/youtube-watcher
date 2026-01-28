"""
YouTube URL utilities for extracting channel IDs and video IDs from various URL formats.
"""

import re
import httpx
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type


# Common HTTP headers for YouTube requests
HTTP_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; YouTubeWatcher/1.0; +https://github.com/thejudge22/youtube-watcher)"
}


async def extract_channel_id(url: str, timeout: float = 10.0) -> str:
    """
    Extract channel ID from various YouTube URL formats.

    Supported formats:
    - https://www.youtube.com/channel/UC... (direct channel ID)
    - https://www.youtube.com/@username (handle format)
    - https://www.youtube.com/c/channelname (custom URL)
    - https://www.youtube.com/user/username (legacy)

    Args:
        url: YouTube channel URL

    Returns:
        Channel ID string

    Raises:
        ValueError: If URL format is not recognized or channel ID cannot be extracted
    """
    url = url.strip()
    
    # Direct channel ID format: /channel/UC...
    channel_match = re.match(r'https?://(?:www\.)?youtube\.com/channel/([A-Za-z0-9_-]{24})', url)
    if channel_match:
        return channel_match.group(1)
    
    # Handle format: /@username
    handle_match = re.match(r'https?://(?:www\.)?youtube\.com/@([A-Za-z0-9_.-]+)', url)
    if handle_match:
        return await _fetch_channel_id_from_handle(handle_match.group(1), timeout=timeout)

    # Custom URL format: /c/channelname
    custom_match = re.match(r'https?://(?:www\.)?youtube\.com/c/([A-Za-z0-9_.-]+)', url)
    if custom_match:
        return await _fetch_channel_id_from_custom_url(custom_match.group(1), timeout=timeout)

    # Legacy user format: /user/username
    user_match = re.match(r'https?://(?:www\.)?youtube\.com/user/([A-Za-z0-9_.-]+)', url)
    if user_match:
        return await _fetch_channel_id_from_user(user_match.group(1), timeout=timeout)
    
    raise ValueError(f"Unrecognized YouTube channel URL format: {url}")


async def _fetch_channel_id_from_handle(handle: str, timeout: float = 10.0) -> str:
    """
    Fetch channel ID from a YouTube handle by fetching the page and extracting the ID.

    Args:
        handle: YouTube handle (without @ prefix)

    Returns:
        Channel ID string

    Raises:
        ValueError: If channel ID cannot be found in the page
    """
    url = f"https://www.youtube.com/@{handle}"
    return await _fetch_channel_id_from_page(url, timeout=timeout)


async def _fetch_channel_id_from_custom_url(custom_name: str, timeout: float = 10.0) -> str:
    """
    Fetch channel ID from a custom YouTube URL.

    Args:
        custom_name: Custom channel name

    Returns:
        Channel ID string

    Raises:
        ValueError: If channel ID cannot be found in the page
    """
    url = f"https://www.youtube.com/c/{custom_name}"
    return await _fetch_channel_id_from_page(url, timeout=timeout)


async def _fetch_channel_id_from_user(username: str, timeout: float = 10.0) -> str:
    """
    Fetch channel ID from a legacy YouTube username URL.

    Args:
        username: YouTube username

    Returns:
        Channel ID string

    Raises:
        ValueError: If channel ID cannot be found in the page
    """
    url = f"https://www.youtube.com/user/{username}"
    return await _fetch_channel_id_from_page(url, timeout=timeout)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type((httpx.HTTPError, httpx.TimeoutException)),
)
async def _fetch_channel_id_from_page(url: str, timeout: float = 10.0) -> str:
    """
    Fetch a YouTube page and extract the channel ID from the page content.

    The channel ID can be found in various places in the page:
    - In meta tags: <meta itemprop="channelId" content="UC...">
    - In the page's embedded JSON data

    Retries up to 3 times with exponential backoff on HTTP errors.

    Args:
        url: YouTube channel page URL

    Returns:
        Channel ID string

    Raises:
        ValueError: If channel ID cannot be found in the page
    """
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=HTTP_HEADERS) as client:
        response = await client.get(url)
        response.raise_for_status()
        html = response.text
        
        # Try to extract from meta tag
        meta_match = re.search(r'<meta[^>]*itemprop="channelId"[^>]*content="([^"]+)"', html)
        if meta_match:
            return meta_match.group(1)
        
        # Try to extract from ytInitialData JSON
        data_match = re.search(r'var ytInitialData = ({.+?});', html)
        if data_match:
            import json
            try:
                data = json.loads(data_match.group(1))
                # Navigate through the JSON structure to find channel ID
                # The structure can vary, so we search for a UC... pattern
                json_str = json.dumps(data)
                channel_id_match = re.search(r'UC[A-Za-z0-9_-]{22}', json_str)
                if channel_id_match:
                    return channel_id_match.group(0)
            except json.JSONDecodeError:
                pass
        
        raise ValueError(f"Could not extract channel ID from page: {url}")


def get_rss_url(channel_id: str) -> str:
    """
    Build the RSS feed URL for a YouTube channel.

    Args:
        channel_id: YouTube channel ID

    Returns:
        RSS feed URL
    """
    return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"


def get_channel_url(channel_id: str) -> str:
    """
    Build the channel URL for a YouTube channel.

    Args:
        channel_id: YouTube channel ID

    Returns:
        Channel URL
    """
    return f"https://www.youtube.com/channel/{channel_id}"


def extract_video_id(url: str) -> str:
    """
    Extract video ID from a YouTube URL.

    Supported formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://www.youtube.com/v/VIDEO_ID
    - https://www.youtube.com/shorts/VIDEO_ID

    Args:
        url: YouTube video URL

    Returns:
        Video ID string

    Raises:
        ValueError: If URL format is not recognized
    """
    url = url.strip()
    
    # Standard watch URL: /watch?v=VIDEO_ID
    watch_match = re.match(r'https?://(?:www\.)?youtube\.com/watch\?.*v=([A-Za-z0-9_-]{11})', url)
    if watch_match:
        return watch_match.group(1)
    
    # Short URL: youtu.be/VIDEO_ID
    short_match = re.match(r'https?://youtu\.be/([A-Za-z0-9_-]{11})', url)
    if short_match:
        return short_match.group(1)
    
    # Embed URL: /embed/VIDEO_ID
    embed_match = re.match(r'https?://(?:www\.)?youtube\.com/embed/([A-Za-z0-9_-]{11})', url)
    if embed_match:
        return embed_match.group(1)
    
    # Legacy v parameter: /v/VIDEO_ID
    v_match = re.match(r'https?://(?:www\.)?youtube\.com/v/([A-Za-z0-9_-]{11})', url)
    if v_match:
        return v_match.group(1)
    
    # Shorts URL: /shorts/VIDEO_ID
    shorts_match = re.match(r'https?://(?:www\.)?youtube\.com/shorts/([A-Za-z0-9_-]{11})', url)
    if shorts_match:
        return shorts_match.group(1)
    
    raise ValueError(f"Unrecognized YouTube video URL format: {url}")


def get_video_url(video_id: str) -> str:
    """
    Build the watch URL for a YouTube video.

    Args:
        video_id: YouTube video ID

    Returns:
        Video watch URL
    """
    return f"https://www.youtube.com/watch?v={video_id}"


def extract_playlist_id(url: str) -> str:
    """
    Extract playlist ID from a YouTube playlist URL.

    Supported formats:
    - https://www.youtube.com/playlist?list=PLxxx
    - https://youtube.com/playlist?list=PLxxx
    - https://www.youtube.com/watch?v=xxx&list=PLxxx
    - https://youtu.be/xxx?list=PLxxx

    Args:
        url: YouTube playlist URL

    Returns:
        Playlist ID string

    Raises:
        ValueError: If URL format is not recognized or playlist ID cannot be extracted
    """
    url = url.strip()

    # Standard playlist URL: /playlist?list=PLAYLIST_ID
    playlist_match = re.match(r'https?://(?:www\.)?youtube\.com/playlist\?.*list=([A-Za-z0-9_-]+)', url)
    if playlist_match:
        return playlist_match.group(1)

    # Watch URL with playlist parameter: /watch?v=VIDEO_ID&list=PLAYLIST_ID
    watch_match = re.match(r'https?://(?:www\.)?youtube\.com/watch\?.*list=([A-Za-z0-9_-]+)', url)
    if watch_match:
        return watch_match.group(1)

    # Short URL with playlist parameter: youtu.be/VIDEO_ID?list=PLAYLIST_ID
    short_match = re.match(r'https?://youtu\.be/[A-Za-z0-9_-]+\?.*list=([A-Za-z0-9_-]+)', url)
    if short_match:
        return short_match.group(1)

    # Embed URL with playlist parameter: /embed/VIDEO_ID?list=PLAYLIST_ID
    embed_match = re.match(r'https?://(?:www\.)?youtube\.com/embed/[A-Za-z0-9_-]+\?.*list=([A-Za-z0-9_-]+)', url)
    if embed_match:
        return embed_match.group(1)

    raise ValueError(f"Unrecognized YouTube playlist URL format: {url}")
