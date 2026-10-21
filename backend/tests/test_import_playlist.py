"""Integration tests for playlist import functionality."""
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
@pytest.mark.integration
async def test_import_playlist_invalid_url(client):
    """Test importing from an invalid playlist URL."""
    response = await client.post(
        "/api/import-export/import/playlist",
        json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["total"] == 0
    assert result["imported"] == 0
    assert result["skipped"] == 0
    assert len(result["errors"]) > 0
    assert "playlist" in result["errors"][0].lower()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_import_playlist_empty_url(client):
    """Test importing from an empty URL."""
    response = await client.post(
        "/api/import-export/import/playlist",
        json={"url": ""}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["total"] == 0
    assert result["imported"] == 0
    assert result["skipped"] == 0
    assert len(result["errors"]) > 0


@pytest.mark.asyncio
@pytest.mark.integration
async def test_import_playlist_real_playlist(client, db_session):
    """Test importing videos from a real YouTube playlist.
    
    Uses a known public playlist for testing.
    """
    # Use the example playlist from the issue
    response = await client.post(
        "/api/import-export/import/playlist",
        json={"url": "https://www.youtube.com/playlist?list=PLSxDqWtr5iWGc1uDbQxAzRHygDAqbx5nc"}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["total"] > 0
    assert result["imported"] >= 0
    assert result["skipped"] >= 0
    assert isinstance(result["errors"], list)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_import_playlist_duplicate_videos(client, db_session, sample_video):
    """Test that duplicate videos are skipped."""
    # First, create a video that might be in the playlist
    # We'll use a known video ID from a test playlist
    # This test assumes the playlist contains this video ID
    pass  # Full implementation would require mocking or a stable test playlist


@pytest.mark.asyncio
@pytest.mark.integration
async def test_import_playlist_does_not_subscribe(client, db_session):
    """Importing a playlist saves videos but never subscribes to their channels."""
    response = await client.post(
        "/api/import-export/import/playlist",
        json={"url": "https://www.youtube.com/playlist?list=PLSxDqWtr5iWGc1uDbQxAzRHygDAqbx5nc"}
    )
    assert response.status_code == 200
    result = response.json()
    assert result["imported"] > 0

    from app.models.channel import Channel
    from sqlalchemy import select

    channels_result = await db_session.execute(select(Channel))
    assert channels_result.scalars().all() == []
