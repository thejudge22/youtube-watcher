import pytest
from datetime import datetime, UTC
from app.models.channel import Channel
from app.models.video import Video


class TestListInboxVideos:
    @pytest.mark.asyncio
    async def test_list_inbox_videos_empty(self, client):
        """Test listing inbox videos when database is empty."""
        response = await client.get("/api/videos/inbox")
        assert response.status_code == 200
        assert response.json() == []
    
    @pytest.mark.asyncio
    async def test_list_inbox_videos_with_data(self, client, sample_video):
        """Test listing inbox videos with existing data."""
        response = await client.get("/api/videos/inbox")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "inbox"
        assert data[0]["title"] == "Test Video"


class TestListSavedVideos:
    @pytest.mark.asyncio
    async def test_list_saved_videos_empty(self, client):
        """Test listing saved videos when database is empty."""
        response = await client.get("/api/videos/saved")
        assert response.status_code == 200
        assert response.json() == []
    
    @pytest.mark.asyncio
    async def test_list_saved_videos_with_data(self, client, db_session, sample_channel):
        """Test listing saved videos with existing data."""
        # Create a saved video
        video = Video(
            youtube_video_id="saved-video-123",
            channel_id=sample_channel.id,
            title="Saved Video",
            video_url="https://www.youtube.com/watch?v=saved-video-123",
            published_at=datetime.now(UTC),
            status="saved",
            saved_at=datetime.now(UTC)
        )
        db_session.add(video)
        await db_session.commit()
        
        response = await client.get("/api/videos/saved")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["status"] == "saved"
        assert data[0]["title"] == "Saved Video"
    
    @pytest.mark.asyncio
    async def test_list_saved_videos_with_channel_filter(self, client, db_session, sample_channel):
        """Test listing saved videos with channel filter."""
        # Create another channel
        channel2 = Channel(
            youtube_channel_id="UC-test456",
            name="Test Channel 2",
            rss_url="https://www.youtube.com/feeds/videos.xml?channel_id=UC-test456",
            youtube_url="https://www.youtube.com/channel/UC-test456"
        )
        db_session.add(channel2)
        await db_session.commit()
        await db_session.refresh(channel2)
        
        # Create videos for both channels
        video1 = Video(
            youtube_video_id="saved-video-1",
            channel_id=sample_channel.id,
            title="Saved Video 1",
            video_url="https://www.youtube.com/watch?v=saved-video-1",
            published_at=datetime.now(UTC),
            status="saved",
            saved_at=datetime.now(UTC)
        )
        video2 = Video(
            youtube_video_id="saved-video-2",
            channel_id=channel2.id,
            title="Saved Video 2",
            video_url="https://www.youtube.com/watch?v=saved-video-2",
            published_at=datetime.now(UTC),
            status="saved",
            saved_at=datetime.now(UTC)
        )
        db_session.add(video1)
        db_session.add(video2)
        await db_session.commit()
        
        # Filter by first channel
        response = await client.get(f"/api/videos/saved?channel_id={sample_channel.id}")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == "Saved Video 1"
    
    @pytest.mark.asyncio
    async def test_list_saved_videos_invalid_sort_by(self, client):
        """Test listing saved videos with invalid sort_by parameter."""
        response = await client.get("/api/videos/saved?sort_by=invalid")
        assert response.status_code == 400
        assert "sort_by must be" in response.json()["detail"]
    
    @pytest.mark.asyncio
    async def test_list_saved_videos_invalid_order(self, client):
        """Test listing saved videos with invalid order parameter."""
        response = await client.get("/api/videos/saved?order=invalid")
        assert response.status_code == 400
        assert "order must be" in response.json()["detail"]


class TestSaveVideo:
    @pytest.mark.asyncio
    async def test_save_video(self, client, sample_video):
        """Test saving a video."""
        response = await client.post(f"/api/videos/{sample_video.id}/save")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "saved"
        assert data["saved_at"] is not None
        assert data["discarded_at"] is None
    
    @pytest.mark.asyncio
    async def test_save_nonexistent_video(self, client):
        """Test saving a video that doesn't exist."""
        response = await client.post("/api/videos/nonexistent-id/save")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestDiscardVideo:
    @pytest.mark.asyncio
    async def test_discard_video(self, client, sample_video):
        """Test discarding a video."""
        response = await client.post(f"/api/videos/{sample_video.id}/discard")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "discarded"
        assert data["discarded_at"] is not None
        assert data["saved_at"] is None
    
    @pytest.mark.asyncio
    async def test_discard_nonexistent_video(self, client):
        """Test discarding a video that doesn't exist."""
        response = await client.post("/api/videos/nonexistent-id/discard")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]


class TestBulkSaveVideos:
    @pytest.mark.asyncio
    async def test_bulk_save_videos(self, client, db_session, sample_channel):
        """Test bulk saving multiple videos."""
        # Create multiple videos
        video_ids = []
        for i in range(3):
            video = Video(
                youtube_video_id=f"video-{i}",
                channel_id=sample_channel.id,
                title=f"Video {i}",
                video_url=f"https://www.youtube.com/watch?v=video-{i}",
                published_at=datetime.now(UTC),
                status="inbox"
            )
            db_session.add(video)
            await db_session.flush()
            video_ids.append(video.id)
        await db_session.commit()
        
        # Bulk save videos
        response = await client.post(
            "/api/videos/bulk-save",
            json={"video_ids": video_ids}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        for video in data:
            assert video["status"] == "saved"
            assert video["saved_at"] is not None
    
    @pytest.mark.asyncio
    async def test_bulk_save_empty_list(self, client):
        """Test bulk saving with empty list."""
        response = await client.post(
            "/api/videos/bulk-save",
            json={"video_ids": []}
        )
        assert response.status_code == 200
        assert response.json() == []


class TestBulkDiscardVideos:
    @pytest.mark.asyncio
    async def test_bulk_discard_videos(self, client, db_session, sample_channel):
        """Test bulk discarding multiple videos."""
        # Create multiple videos
        video_ids = []
        for i in range(3):
            video = Video(
                youtube_video_id=f"video-{i}",
                channel_id=sample_channel.id,
                title=f"Video {i}",
                video_url=f"https://www.youtube.com/watch?v=video-{i}",
                published_at=datetime.now(UTC),
                status="inbox"
            )
            db_session.add(video)
            await db_session.flush()
            video_ids.append(video.id)
        await db_session.commit()
        
        # Bulk discard videos
        response = await client.post(
            "/api/videos/bulk-discard",
            json={"video_ids": video_ids}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        for video in data:
            assert video["status"] == "discarded"
            assert video["discarded_at"] is not None
    
    @pytest.mark.asyncio
    async def test_bulk_discard_empty_list(self, client):
        """Test bulk discarding with empty list."""
        response = await client.post(
            "/api/videos/bulk-discard",
            json={"video_ids": []}
        )
        assert response.status_code == 200
        assert response.json() == []


class TestAddVideoFromUrl:
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_add_video_from_url(self, client):
        """Test adding a video from a YouTube URL."""
        # This test requires network access
        response = await client.post(
            "/api/videos/from-url",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        )
        assert response.status_code == 201
        data = response.json()
        assert data["youtube_video_id"] == "dQw4w9WgXcQ"
        assert data["status"] == "saved"
        assert data["saved_at"] is not None
    
    @pytest.mark.asyncio
    async def test_add_video_from_invalid_url(self, client):
        """Test adding a video with an invalid URL."""
        response = await client.post(
            "/api/videos/from-url",
            json={"url": "https://example.com/invalid"}
        )
        assert response.status_code == 400
        assert "detail" in response.json()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_add_existing_video_from_url(self, client):
        """Test adding a video that already exists."""
        # Add video first time
        response1 = await client.post(
            "/api/videos/from-url",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        )
        assert response1.status_code == 201
        
        # Add same video again
        response2 = await client.post(
            "/api/videos/from-url",
            json={"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
        )
        assert response2.status_code == 200  # Returns existing video
        assert response1.json()["id"] == response2.json()["id"]


class TestDeleteVideo:
    @pytest.mark.asyncio
    async def test_delete_existing_video(self, client, sample_video):
        """Test deleting an existing video."""
        response = await client.delete(f"/api/videos/{sample_video.id}")
        assert response.status_code == 204
        
        # Verify it's deleted
        response = await client.get("/api/videos/inbox")
        assert response.status_code == 200
        assert len(response.json()) == 0
    
    @pytest.mark.asyncio
    async def test_delete_nonexistent_video(self, client):
        """Test deleting a video that doesn't exist."""
        response = await client.delete("/api/videos/nonexistent-id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"]