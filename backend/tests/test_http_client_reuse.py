"""Batch operations reuse one HTTP client instead of opening one per request."""
from unittest.mock import AsyncMock, MagicMock

from app.services.rss_parser import fetch_videos
from app.services.shorts_detector import detect_shorts_batch_http

FEED = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom" xmlns:yt="http://www.youtube.com/xml/schemas/2015">
  <title>G Channel</title><yt:channelId>UC-g</yt:channelId>
  <entry><yt:videoId>ggggggggggg</yt:videoId><title>G</title>
    <published>2026-01-01T00:00:00+00:00</published></entry>
</feed>"""


async def test_shorts_batch_uses_one_client(mocker):
    client = AsyncMock()
    client.get = AsyncMock(return_value=MagicMock(status_code=303))
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=False)
    constructor = mocker.patch("httpx.AsyncClient", return_value=client)

    results = await detect_shorts_batch_http(["a" * 11, "b" * 11, "c" * 11])

    assert list(results.values()) == [False, False, False]
    assert constructor.call_count == 1


async def test_fetch_videos_uses_passed_client(mocker):
    mocker.patch("httpx.AsyncClient", side_effect=AssertionError("new client"))
    response = MagicMock(content=FEED)
    response.raise_for_status = MagicMock()
    client = AsyncMock()
    client.get = AsyncMock(return_value=response)

    videos = await fetch_videos("https://www.youtube.com/feeds/videos.xml?channel_id=UC-g", client=client)

    assert [v.video_id for v in videos] == ["g" * 11]
