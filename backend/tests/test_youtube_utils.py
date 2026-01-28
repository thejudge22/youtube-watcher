import pytest
import asyncio
from app.services.youtube_utils import (
    extract_channel_id,
    get_rss_url,
    extract_video_id,
    get_video_url,
    extract_playlist_id,
)

# Test extract_video_id - Synchronous (no network)
class TestExtractVideoId:
    def test_standard_watch_url(self):
        assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
        # Test specific user example
        assert extract_video_id("https://www.youtube.com/watch?v=gYFZ4HYTsZI") == "gYFZ4HYTsZI"
    
    def test_short_url(self):
        assert extract_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    
    def test_shorts_url(self):
        assert extract_video_id("https://www.youtube.com/shorts/mccyHdidiG8") == "mccyHdidiG8"
    
    def test_embed_url(self):
        assert extract_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    
    def test_v_url(self):
        assert extract_video_id("https://www.youtube.com/v/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    
    def test_with_extra_params(self):
        assert extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=30s") == "dQw4w9WgXcQ"
    
    def test_invalid_url_raises(self):
        with pytest.raises(ValueError):
            extract_video_id("https://example.com/video")

# Test get_video_url
class TestGetVideoUrl:
    def test_builds_correct_url(self):
        assert get_video_url("dQw4w9WgXcQ") == "https://www.youtube.com/watch?v=dQw4w9WgXcQ"

# Test get_rss_url
class TestGetRssUrl:
    def test_builds_correct_url(self):
        assert get_rss_url("UCxyz123456789012345678") == "https://www.youtube.com/feeds/videos.xml?channel_id=UCxyz123456789012345678"

# Test extract_channel_id - Async (some require network)
class TestExtractChannelId:
    @pytest.mark.asyncio
    async def test_direct_channel_url(self):
        result = await extract_channel_id("https://www.youtube.com/channel/UC-lHJZR3Gqxm24_Vd_AJ5Yw")
        assert result == "UC-lHJZR3Gqxm24_Vd_AJ5Yw"
    
    @pytest.mark.asyncio
    async def test_invalid_url_raises(self):
        with pytest.raises(ValueError):
            await extract_channel_id("https://example.com/channel")
    
    # These tests require network access
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_handle_url(self):
        # Use a known, stable YouTube channel
        result = await extract_channel_id("https://www.youtube.com/@Google")
        assert result.startswith("UC")
        assert len(result) == 24
        
        # Test specific user example
        result2 = await extract_channel_id("https://www.youtube.com/@JoshuaWeissman")
        assert result2.startswith("UC")
        assert len(result2) == 24
    
    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_handle_with_dots(self):
        # This is the case that failed according to the bug report
        result = await extract_channel_id("https://www.youtube.com/@post.10")
        assert result.startswith("UC")
        assert len(result) == 24


# Test extract_playlist_id - Synchronous (no network)
class TestExtractPlaylistId:
    def test_standard_playlist_url(self):
        assert extract_playlist_id(
            "https://www.youtube.com/playlist?list=PLSxDqWtr5iWGc1uDbQxAzRHygDAqbx5nc"
        ) == "PLSxDqWtr5iWGc1uDbQxAzRHygDAqbx5nc"

    def test_playlist_url_without_www(self):
        assert extract_playlist_id(
            "https://youtube.com/playlist?list=PLSxDqWtr5iWGc1uDbQxAzRHygDAqbx5nc"
        ) == "PLSxDqWtr5iWGc1uDbQxAzRHygDAqbx5nc"

    def test_watch_url_with_playlist(self):
        assert extract_playlist_id(
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PLSxDqWtr5iWGc1uDbQxAzRHygDAqbx5nc"
        ) == "PLSxDqWtr5iWGc1uDbQxAzRHygDAqbx5nc"

    def test_watch_url_with_playlist_first_param(self):
        assert extract_playlist_id(
            "https://www.youtube.com/watch?list=PLSxDqWtr5iWGc1uDbQxAzRHygDAqbx5nc&v=dQw4w9WgXcQ"
        ) == "PLSxDqWtr5iWGc1uDbQxAzRHygDAqbx5nc"

    def test_youtu_be_with_playlist(self):
        assert extract_playlist_id(
            "https://youtu.be/dQw4w9WgXcQ?list=PLSxDqWtr5iWGc1uDbQxAzRHygDAqbx5nc"
        ) == "PLSxDqWtr5iWGc1uDbQxAzRHygDAqbx5nc"

    def test_embed_url_with_playlist(self):
        assert extract_playlist_id(
            "https://www.youtube.com/embed/dQw4w9WgXcQ?list=PLSxDqWtr5iWGc1uDbQxAzRHygDAqbx5nc"
        ) == "PLSxDqWtr5iWGc1uDbQxAzRHygDAqbx5nc"

    def test_invalid_url_raises(self):
        with pytest.raises(ValueError):
            extract_playlist_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ")

    def test_invalid_domain_raises(self):
        with pytest.raises(ValueError):
            extract_playlist_id("https://example.com/playlist?list=PLxxx")