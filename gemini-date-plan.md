# Implementation Plan: Fix Video Date & Metadata Issue

**Goal:** Fix the issue where videos imported via URL have incorrect `published_at` dates (defaulting to "now") and missing descriptions.
**Approach:** Replace the limited YouTube oEmbed integration with `yt-dlp`. This library is the industry standard for extracting YouTube metadata reliably without requiring an official YouTube Data API key.

## 1. Dependency Management

We need to add `yt-dlp` to the backend dependencies.

*   **File:** `backend/requirements.txt`
*   **Action:** Add `yt-dlp>=2024.0.0` (or latest stable).
*   **Rationale:** `yt-dlp` is actively maintained and handles YouTube's frequent HTML structure changes better than custom regex scraping.

## 2. Code Implementation

Update the RSS parser service to use `yt-dlp` for single video fetching.

*   **File:** `backend/app/services/rss_parser.py`
*   **Target Function:** `fetch_video_by_id`

### detailed Instructions for the LLM:

1.  **Imports:** Remove `httpx` usage from `fetch_video_by_id` (though it might still be used for RSS fetching). Import `yt_dlp`.
2.  **Configuration:** Configure `yt_dlp.YoutubeDL` with the following options to ensure speed and prevent downloading:
    ```python
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'skip_download': True,
        'extract_flat': False,  # We need full info for description/tags
    }
    ```
3.  **Extraction Logic:**
    *   Use `with yt_dlp.YoutubeDL(ydl_opts) as ydl: info = ydl.extract_info(video_url, download=False)`
    *   Extract fields:
        *   `id`: Video ID
        *   `title`: Video Title
        *   `description`: Full video description (fixes the missing description issue)
        *   `uploader`: Channel Name
        *   `channel_id`: Channel ID
        *   `thumbnail`: Best thumbnail URL
        *   `upload_date`: Returns string "YYYYMMDD". **Crucial:** Parse this string into a `datetime` object with UTC timezone.
4.  **Error Handling:** Wrap the extraction in try/except blocks to catch `yt_dlp.utils.DownloadError` and re-raise as `ValueError` (to match existing interface) or a custom `ExternalServiceError`.

## 3. Testing Updates

Since we are changing the implementation strategy, existing tests mocking `httpx` for this function will fail.

*   **File:** `backend/tests/test_rss_parser.py`
*   **Action:**
    1.  Locate tests targeting `fetch_video_by_id`.
    2.  Replace `httpx` mocking with `unittest.mock.patch` for `yt_dlp.YoutubeDL`.
    3.  Mock the return value of `extract_info` to return a sample dictionary resembling `yt-dlp` output:
        ```python
        {
            'id': 'video123',
            'title': 'Test Video',
            'uploader': 'Test Channel',
            'channel_id': 'channel123',
            'upload_date': '20250101',
            'description': 'Test Description',
            'thumbnail': 'http://example.com/thumb.jpg'
        }
        ```
    4.  Verify that the parsed `published_at` in the result matches `2025-01-01` in UTC.

## 4. Verification Steps

1.  Run `pip install -r backend/requirements.txt` inside the container/environment.
2.  Run `pytest backend/tests/test_rss_parser.py` to ensure the new logic works.
3.  (Manual) Use the "Add Video from URL" feature in the UI with a real YouTube URL and verify the "Published" date is correct (not "Just now").
