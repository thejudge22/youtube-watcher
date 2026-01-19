import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone
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
    
    @pytest.mark.asyncio
    async def test_fetch_video_by_id_with_mock(self):
        """Test fetch_video_by_id with mocked yt-dlp to verify date parsing."""
        # Mock yt-dlp response
        mock_info = {
            'id': 'video123',
            'title': 'Test Video',
            'uploader': 'Test Channel',
            'channel_id': 'channel123',
            'upload_date': '20250101',
            'description': 'Test Description',
            'thumbnail': 'http://example.com/thumb.jpg'
        }
        
        # Mock YoutubeDL context manager
        mock_ydl = MagicMock()
        mock_ydl.extract_info.return_value = mock_info
        
        with patch('app.services.rss_parser.yt_dlp.YoutubeDL') as mock_ytdl_class:
            mock_ytdl_class.return_value.__enter__.return_value = mock_ydl
            
            # Call the function
            video = await fetch_video_by_id("video123")
            
            # Verify the results
            assert video.video_id == "video123"
            assert video.title == "Test Video"
            assert video.channel_name == "Test Channel"
            assert video.channel_id == "channel123"
            assert video.description == "Test Description"
            assert video.thumbnail_url == "http://example.com/thumb.jpg"
            
            # Verify the date was parsed correctly (2025-01-01 UTC)
            expected_date = datetime(2025, 1, 1, tzinfo=timezone.utc)
            assert video.published_at == expected_date