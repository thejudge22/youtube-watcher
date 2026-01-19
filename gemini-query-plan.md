# Implementation Plan: Optimize & Abstract Queries

**Goal:** abstract repetitive query construction logic (filtering, sorting, pagination) into a reusable service layer. This addresses the "Repetition" and "Optimize Queries" recommendations.
**Current State:** `list_inbox_videos`, `list_saved_videos`, and `list_discarded_videos` in `routers/videos.py` each manually build SQLAlchemy queries with repetitive `limit`, `offset`, and `order_by` logic.
**Approach:** Create a `VideoService` to handle query construction.

## 1. Create Video Service

*   **File:** `backend/app/services/video_service.py` (New File)
*   **Class:** `VideoService`
*   **Methods:**
    1.  `get_videos(db: AsyncSession, status: str, limit: int, offset: int, channel_id: Optional[str] = None, sort_by: Optional[str] = None, order: str = 'desc')`
        *   Base query: `select(Video).options(selectinload(Video.channel))`
        *   Filter by `status`.
        *   Filter by `channel_id` (if provided).
        *   Apply Sorting:
            *   Handle `sort_by` ('published_at', 'saved_at', 'discarded_at').
            *   Handle `order` ('asc', 'desc').
        *   Apply Pagination (`limit`, `offset`).
        *   Execute and return `scalars().all()`.
    2.  `get_discarded_videos(db: AsyncSession, cutoff_date: datetime, limit: int, offset: int)`
        *   Specific logic for the "discarded since X days" query.

## 2. Refactor Video Router

Update `backend/app/routers/videos.py` to delegate data fetching to the new service.

*   **Imports:** Import `VideoService` (or the functions if you choose a functional approach).
*   **Endpoints to Update:**
    *   `list_inbox_videos`: Call `VideoService.get_videos(..., status='inbox')`.
    *   `list_saved_videos`: Call `VideoService.get_videos(..., status='saved')`.
    *   `list_discarded_videos`: Call `VideoService.get_discarded_videos(...)`.
*   **Cleanup:** Remove the raw SQLAlchemy `select` construction logic from the router endpoints.

## 3. Review `selectinload` Usage

*   **Context:** The review asked to verify `selectinload` efficiency.
*   **Action:** In `VideoService`, ensure `options(selectinload(Video.channel))` is used.
*   **Rationale:** For fetching lists of videos (10-100 items), `selectinload` is efficient as it issues exactly one extra query to fetch referenced channels, avoiding N+1 issues and cartesian products associated with `joinedload`.

## 4. Verification

*   **Run Tests:** `pytest backend/tests/test_api_videos.py`.
*   **Validation:** Ensure filtering and sorting still work as expected via the tests.
