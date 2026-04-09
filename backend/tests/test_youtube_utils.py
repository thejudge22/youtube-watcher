import pytest
import asyncio
from app.services.youtube_utils import (
    extract_channel_id,
    get_rss_url,
    extract_video_id,
    get_video_url,
    extract_playlist_id,
    _fetch_channel_id_from_page,
    YOUTUBE_COOKIES,
    HTTP_HEADERS,
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


# Test consent cookie handling (Issue #44)
class TestConsentCookieHandling:
    """Tests for EU cookie consent bypass (Issue #44)."""
    
    def test_youtube_cookies_defined(self):
        """Verify consent cookies are defined."""
        assert "SOCS" in YOUTUBE_COOKIES
        assert YOUTUBE_COOKIES["SOCS"]  # Not empty
    
    def test_consent_cookies_have_required_keys(self):
        """Verify all required consent cookies are present."""
        assert "SOCS" in YOUTUBE_COOKIES
        assert "CONSENT" in YOUTUBE_COOKIES
    
    def test_socs_cookie_value_is_valid_base64(self):
        """Verify SOCS cookie looks like valid base64 (no padding issues)."""
        socs_value = YOUTUBE_COOKIES["SOCS"]
        # Should be a non-empty string with valid base64 characters
        assert len(socs_value) > 0
        import re
        assert re.match(r'^[A-Za-z0-9_-]+$', socs_value)
    
    def test_http_headers_browser_like(self):
        """Verify HTTP headers use browser-like User-Agent."""
        assert "Mozilla/5.0" in HTTP_HEADERS["User-Agent"]
        assert "Chrome" in HTTP_HEADERS["User-Agent"]
        assert "Accept-Language" in HTTP_HEADERS
        assert "en-US" in HTTP_HEADERS["Accept-Language"]
    
    @pytest.mark.asyncio
    async def test_fetch_channel_id_sends_cookies(self, mocker):
        """Verify that _fetch_channel_id_from_page sends consent cookies."""
        mock_response = mocker.MagicMock()
        mock_response.text = '<meta itemprop="channelId" content="UCxxxxxxxxxxxxxxxxxxxxxxxx">'
        mock_response.url = "https://www.youtube.com/@test"
        mock_response.raise_for_status = mocker.MagicMock()
        
        mock_client = mocker.AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = mocker.AsyncMock(return_value=False)
        
        mock_async_client = mocker.patch("httpx.AsyncClient", return_value=mock_client)
        
        result = await _fetch_channel_id_from_page("https://www.youtube.com/@test")
        
        # Verify AsyncClient was called with cookies parameter
        call_kwargs = mock_async_client.call_args[1]
        assert "cookies" in call_kwargs
        assert call_kwargs["cookies"] == YOUTUBE_COOKIES
    
    @pytest.mark.asyncio
    async def test_consent_page_detection_youtube(self, mocker):
        """Verify consent.youtube.com is detected and raises clear error."""
        mock_response = mocker.MagicMock()
        mock_response.text = '<html>consent page</html>'
        mock_response.url = "https://consent.youtube.com/m?continue=https://www.youtube.com/@test"
        mock_response.raise_for_status = mocker.MagicMock()
        
        mock_client = mocker.AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = mocker.AsyncMock(return_value=False)
        
        mocker.patch("httpx.AsyncClient", return_value=mock_client)
        
        with pytest.raises(ValueError, match="cookie consent"):
            await _fetch_channel_id_from_page("https://www.youtube.com/@test")
    
    @pytest.mark.asyncio
    async def test_consent_page_detection_google(self, mocker):
        """Verify consent.google.com is detected and raises clear error."""
        mock_response = mocker.MagicMock()
        mock_response.text = '<html>consent page</html>'
        mock_response.url = "https://consent.google.com/ml?continue=https://www.youtube.com/@test"
        mock_response.raise_for_status = mocker.MagicMock()
        
        mock_client = mocker.AsyncMock()
        mock_client.get.return_value = mock_response
        mock_client.__aenter__ = mocker.AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = mocker.AsyncMock(return_value=False)
        
        mocker.patch("httpx.AsyncClient", return_value=mock_client)
        
        with pytest.raises(ValueError, match="cookie consent"):
            await _fetch_channel_id_from_page("https://www.youtube.com/@test")
