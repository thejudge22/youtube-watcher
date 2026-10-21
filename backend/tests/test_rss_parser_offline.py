"""Offline tests for yt-dlp based fetching (no network)."""
import asyncio
import time

import pytest
import yt_dlp

from app.services import rss_parser
from app.services.rss_parser import fetch_video_by_id

F = "f" * 11
FAKE_INFO = {"title": "T", "uploader": "U", "channel_id": "UC-x", "upload_date": "20260101",
             "webpage_url": "https://www.youtube.com/watch?v=" + F}


async def test_fetch_video_by_id_does_not_block_loop(monkeypatch):
    def slow_extract(url, opts):
        time.sleep(0.3)
        return FAKE_INFO

    monkeypatch.setattr(rss_parser, "_extract_info", slow_extract)
    ticks = 0

    async def ticker():
        nonlocal ticks
        end = time.monotonic() + 0.25
        while time.monotonic() < end:
            await asyncio.sleep(0.01)
            ticks += 1

    await asyncio.gather(fetch_video_by_id(F), ticker())
    assert ticks >= 10


async def test_fetch_video_by_id_passes_socket_timeout(monkeypatch):
    captured = {}

    def fake_extract(url, opts):
        captured.update(opts)
        return FAKE_INFO

    monkeypatch.setattr(rss_parser, "_extract_info", fake_extract)
    await fetch_video_by_id(F, timeout=7.0)
    assert captured["socket_timeout"] == 7.0
    assert captured["extractor_retries"] == 3


async def test_download_error_becomes_value_error_once(monkeypatch):
    calls = 0

    def failing_extract(url, opts):
        nonlocal calls
        calls += 1
        raise yt_dlp.utils.DownloadError("x")

    monkeypatch.setattr(rss_parser, "_extract_info", failing_extract)
    with pytest.raises(ValueError):
        await fetch_video_by_id(F)
    assert calls == 1
