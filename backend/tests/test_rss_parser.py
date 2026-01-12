import pytest
from app.services.rss_parser import fetch_channel_info, fetch_videos, fetch_video_by_id

# Use a known, active YouTube channel for testing
TEST_CHANNEL_ID = "UC-lHJZR3Gqxm24_Vd_AJ5Yw"  # PewDiePie (stable, high-activity channel)

class TestFetchChannelInfo:
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_fetch_channel_info(self):
        info = await fetch_channel_info(TEST_CHANNEL_ID)
        assert info.channel_id == TEST_CHANNEL_ID
        assert info.name  # Should have a name
        # thumbnail_url may or may not be present

class TestFetchVideos:
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_fetch_videos_with_limit(self):
        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={TEST_CHANNEL_ID}"
        videos = await fetch_videos(rss_url, limit=5)
        assert len(videos) <= 5
        for video in videos:
            assert video.video_id
            assert video.title
            assert video.video_url
            assert video.published_at

class TestFetchVideoById:
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_fetch_video_by_id(self):
        # Use a known, stable video
        video = await fetch_video_by_id("dQw4w9WgXcQ")
        assert video.video_id == "dQw4w9WgXcQ"
        assert video.title
        assert video.video_url == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"