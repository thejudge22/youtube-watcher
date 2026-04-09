import pytest
from app.models.channel import Channel


class TestListChannels:
    @pytest.mark.asyncio
    async def test_list_channels_empty(self, client):
        """Test listing channels when database is empty."""
        response = await client.get("/api/channels")
        assert response.status_code == 200
        assert response.json() == []
    
    @pytest.mark.asyncio
    async def test_list_channels_with_data(self, client, sample_channel):
        """Test listing channels with existing data."""
        response = await client.get("/api/channels")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["name"] == "Test Channel"
        assert data[0]["youtube_channel_id"] == "UC-test123"


class TestCreateChannel:
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_channel_with_valid_url(self, client):
        """Test creating a channel with a valid YouTube channel URL."""
        # This test requires network access
        response = await client.post(
            "/api/channels",
            json={"url": "https://www.youtube.com/channel/UC-lHJZR3Gqxm24_Vd_AJ5Yw"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["youtube_channel_id"] == "UC-lHJZR3Gqxm24_Vd_AJ5Yw"
        assert "name" in data
        assert "video_count" in data
    
    @pytest.mark.asyncio
    async def test_create_channel_with_invalid_url(self, client):
        """Test creating a channel with an invalid URL."""
        response = await client.post(
            "/api/channels",
            json={"url": "https://example.com/invalid"}
        )
        assert response.status_code == 400
        assert "error" in response.json()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_create_duplicate_channel(self, client, db_session):
        """Test creating a channel that already exists."""
        # Create a channel with a real YouTube ID first
        from app.models.channel import Channel
        channel = Channel(
            youtube_channel_id="UC-lHJZR3Gqxm24_Vd_AJ5Yw",
            name="PewDiePie",
            rss_url="https://www.youtube.com/feeds/videos.xml?channel_id=UC-lHJZR3Gqxm24_Vd_AJ5Yw",
            youtube_url="https://www.youtube.com/channel/UC-lHJZR3Gqxm24_Vd_AJ5Yw"
        )
        db_session.add(channel)
        await db_session.commit()
        
        # Try to create the same channel again
        response = await client.post(
            "/api/channels",
            json={"url": "https://www.youtube.com/channel/UC-lHJZR3Gqxm24_Vd_AJ5Yw"}
        )
        assert response.status_code == 409
        assert "already exists" in response.json()["error"]["message"]


class TestDeleteChannel:
    @pytest.mark.asyncio
    async def test_delete_existing_channel(self, client, sample_channel):
        """Test deleting an existing channel."""
        # Delete the channel
        response = await client.delete(f"/api/channels/{sample_channel.id}")
        assert response.status_code == 204
        
        # Verify it's deleted
        response = await client.get("/api/channels")
        assert response.status_code == 200
        assert len(response.json()) == 0
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_channel(self, client):
        """Test deleting a channel that doesn't exist."""
        response = await client.delete("/api/channels/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404


class TestRefreshChannel:
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_refresh_existing_channel(self, client, db_session):
        """Test refreshing an existing channel."""
        # Create a test channel with a real YouTube channel ID
        channel = Channel(
            youtube_channel_id="UC-lHJZR3Gqxm24_Vd_AJ5Yw",  # PewDiePie - stable channel
            name="PewDiePie",
            rss_url="https://www.youtube.com/feeds/videos.xml?channel_id=UC-lHJZR3Gqxm24_Vd_AJ5Yw",
            youtube_url="https://www.youtube.com/channel/UC-lHJZR3Gqxm24_Vd_AJ5Yw"
        )
        db_session.add(channel)
        await db_session.commit()
        await db_session.refresh(channel)
        
        # Refresh the channel
        response = await client.post(f"/api/channels/{channel.id}/refresh")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == channel.id
        assert "last_checked" in data
    
    @pytest.mark.asyncio
    async def test_refresh_nonexistent_channel(self, client):
        """Test refreshing a channel that doesn't exist."""
        response = await client.post("/api/channels/00000000-0000-0000-0000-000000000000/refresh")
        assert response.status_code == 404


class TestRefreshAllChannels:
    @pytest.mark.asyncio
    async def test_refresh_all_channels_empty(self, client):
        """Test refreshing all channels when database is empty."""
        response = await client.post("/api/channels/refresh-all")
        assert response.status_code == 200
        data = response.json()
        assert data["channels_refreshed"] == 0
        assert data["new_videos_found"] == 0
        assert data["errors"] == []
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_refresh_all_channels_with_data(self, client, db_session):
        """Test refreshing all channels with existing channels."""
        # Create a test channel with a real YouTube channel ID
        channel = Channel(
            youtube_channel_id="UC-lHJZR3Gqxm24_Vd_AJ5Yw",  # PewDiePie - stable channel
            name="PewDiePie",
            rss_url="https://www.youtube.com/feeds/videos.xml?channel_id=UC-lHJZR3Gqxm24_Vd_AJ5Yw",
            youtube_url="https://www.youtube.com/channel/UC-lHJZR3Gqxm24_Vd_AJ5Yw"
        )
        db_session.add(channel)
        await db_session.commit()
        
        # Refresh all channels
        response = await client.post("/api/channels/refresh-all")
        assert response.status_code == 200
        data = response.json()
        assert data["channels_refreshed"] >= 0
        assert "new_videos_found" in data
        assert "errors" in data