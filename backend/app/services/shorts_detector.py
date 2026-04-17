"""
Service for detecting YouTube Shorts.

Two detection methods:
1. URL pattern matching (legacy) — only works when /shorts/ is in the URL
2. HTTP status check (Issue #55) — fast batch detection using YouTube's
   /shorts/{video_id} endpoint which returns 200 for Shorts, 303 (redirect)
   for regular videos, and 404 for unavailable videos.
"""

import asyncio
import re
import logging
from datetime import datetime, timezone
from typing import Optional

import httpx

from .youtube_utils import HTTP_HEADERS, YOUTUBE_COOKIES

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


async def detect_short_http(
    video_id: str,
    timeout: float = 5.0
) -> Optional[bool]:
    """
    Detect if a single video is a Short via HTTP status check.

    YouTube's /shorts/{video_id} endpoint returns:
    - HTTP 200 for actual Shorts
    - HTTP 303 (redirect to /watch?v=...) for regular videos
    - HTTP 404 for unavailable videos

    Args:
        video_id: YouTube video ID (11 chars)
        timeout: Request timeout in seconds

    Returns:
        True = Short, False = not a Short, None = unavailable/error
    """
    url = get_shorts_url(video_id)
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=False,
            headers=HTTP_HEADERS,
            cookies=YOUTUBE_COOKIES
        ) as client:
            response = await client.get(url)

            if response.status_code == 200:
                return True
            elif response.status_code in (303, 301, 302):
                return False
            elif response.status_code == 404:
                logger.debug(f"Video {video_id} returned 404 (unavailable)")
                return None
            else:
                logger.debug(f"Video {video_id} returned unexpected status {response.status_code}")
                return None
    except (httpx.TimeoutException, httpx.HTTPError) as e:
        logger.debug(f"HTTP check failed for {video_id}: {e}")
        return None


async def detect_shorts_batch_http(
    video_ids: list[str],
    timeout: float = 5.0,
    max_concurrent: int = 5
) -> dict[str, Optional[bool]]:
    """
    Detect Shorts status for multiple videos using concurrent HTTP checks.

    Args:
        video_ids: List of YouTube video IDs
        timeout: Per-request timeout in seconds
        max_concurrent: Maximum concurrent HTTP requests

    Returns:
        Dict mapping video_id to detection result:
        - True = Short (HTTP 200)
        - False = not a Short (HTTP 303 redirect)
        - None = unavailable or error
    """
    if not video_ids:
        return {}

    semaphore = asyncio.Semaphore(max_concurrent)

    async def check_one(vid: str) -> tuple[str, Optional[bool]]:
        async with semaphore:
            result = await detect_short_http(vid, timeout=timeout)
            return (vid, result)

    results = await asyncio.gather(*[check_one(vid) for vid in video_ids])
    return {vid: result for vid, result in results}
