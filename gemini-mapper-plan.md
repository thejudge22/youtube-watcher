# Implementation Plan: Centralize Response Mappers

**Goal:** Refactor the video response mapping logic to reduce code duplication and separate concerns.
**Current State:** The `video_to_response` function is defined locally within `backend/app/routers/videos.py`. It accepts a database session (unused) and mixes presentation logic with routing logic.
**Approach:** Move the mapping logic to a dedicated module.

## 1. Create Mapper Module

Create a new file to hold response transformation logic. This promotes reusability and keeps routers focused on request handling.

*   **File:** `backend/app/schemas/mappers.py` (New File)
*   **Content:**
    ```python
    from ..models.video import Video
    from ..schemas.video import VideoResponse

    def map_video_to_response(video: Video) -> VideoResponse:
        """
        Map a Video database model to a VideoResponse schema.
        Handles the optional channel relationship logic.
        """
        channel_name = None
        if video.channel:
            channel_name = video.channel.name
        
        return VideoResponse(
            id=video.id,
            youtube_video_id=video.youtube_video_id,
            channel_id=video.channel_id,
            channel_name=channel_name,
            title=video.title,
            description=video.description,
            thumbnail_url=video.thumbnail_url,
            video_url=video.video_url,
            published_at=video.published_at,
            status=video.status,
            saved_at=video.saved_at,
            discarded_at=video.discarded_at
        )
    ```

## 2. Refactor Video Router

Update the router to use the new mapper function.

*   **File:** `backend/app/routers/videos.py`
*   **Steps:**
    1.  **Import:** Add `from ..schemas.mappers import map_video_to_response`.
    2.  **Remove:** Delete the local `video_to_response` async function.
    3.  **Replace Usage:**
        *   Find all occurrences of `await video_to_response(db, video)`.
        *   Replace with `map_video_to_response(video)`.
        *   **Note:** The original function was `async` but didn't perform any awaitable operations. The new function is synchronous, so remove the `await` keyword in the calls.

## 3. Verification

*   **Run Tests:** Execute `pytest backend/tests/test_api_videos.py`.
*   **Expectation:** All tests should pass without modification, as the external API contract remains unchanged. The refactor is purely internal structure.
