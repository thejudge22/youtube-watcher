"""
Service for detecting YouTube Shorts based on URL pattern.

YouTube Shorts are identified by the /shorts/ URL pattern. This is the most
reliable detection method since all Shorts use this URL format regardless
of their duration (YouTube now allows Shorts of varying lengths).
"""

import re
import logging

logger = logging.getLogger(__name__)

# Shorts URL pattern
SHORTS_URL_PATTERN = re.compile(r'youtube\.com/shorts/')


def is_shorts_url(url: str) -> bool:
    """
    Check if a URL is a Shorts URL.

    Args:
        url: YouTube video URL

    Returns:
        True if URL contains /shorts/ pattern
    """
    return bool(SHORTS_URL_PATTERN.search(url))


def get_shorts_url(video_id: str) -> str:
    """Get the Shorts URL for a video ID."""
    return f"https://www.youtube.com/shorts/{video_id}"


def get_regular_url(video_id: str) -> str:
    """Get the regular watch URL for a video ID."""
    return f"https://www.youtube.com/watch?v={video_id}"


def is_short_from_video_info(video_info: dict) -> bool:
    """
    Determine if a video is a Short from yt-dlp video info dict.

    Checks for /shorts/ in URL fields returned by yt-dlp.

    Args:
        video_info: Dictionary from yt-dlp extract_info

    Returns:
        True if video appears to be a Short
    """
    # Check webpage_url for /shorts/
    webpage_url = video_info.get('webpage_url', '')
    if is_shorts_url(webpage_url):
        return True

    # Check original_url
    original_url = video_info.get('original_url', '')
    if is_shorts_url(original_url):
        return True

    return False
