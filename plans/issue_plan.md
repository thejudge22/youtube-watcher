# GitHub Issues Implementation Plan

This document outlines the implementation plan for all open GitHub issues in the YouTube-Watcher project. Each issue includes an analysis of the current codebase, implementation options with trade-offs, and recommended approaches.

---

## Table of Contents

1. [Issue #3: Import / Export Data](#issue-3-import--export-data)
2. [Issue #5: Saved Videos View Modes](#issue-5-saved-videos-view-modes)
3. [Issue #6: Inbox View Channel Separation](#issue-6-inbox-view-channel-separation)
4. [Issue #7: Add YouTube Playlist Export](#issue-7-add-youtube-playlist-export)

---

## Issue #3: Import / Export Data

**Created:** 2026-01-13
**Priority:** Medium-High (foundational feature)

### Requirements

1. **Export channels** to JSON format
2. **Export saved videos** to JSON format
3. **Import channels** from JSON format
4. **Import saved videos** from JSON format
5. **Import videos from text file** containing YouTube URLs (one per line)

### Current State Analysis

- No import/export functionality exists
- Channels stored in `channels` table with fields: `id`, `youtube_channel_id`, `name`, `rss_url`, `youtube_url`, `thumbnail_url`, `last_checked`, `last_video_id`
- Videos stored in `videos` table with fields: `id`, `youtube_video_id`, `channel_id`, `title`, `description`, `thumbnail_url`, `video_url`, `published_at`, `status`, `saved_at`, `discarded_at`
- Existing endpoint `POST /api/videos/from-url` handles adding single videos from URL

### Implementation Options

#### Option A: Server-Side Only (Recommended)

**Description:** All import/export logic handled by backend API endpoints.

**New Backend Endpoints:**
```
GET  /api/export/channels           → Returns JSON file download
GET  /api/export/saved-videos       → Returns JSON file download
GET  /api/export/all                → Returns combined JSON file download
POST /api/import/channels           → Accepts JSON upload
POST /api/import/videos             → Accepts JSON upload
POST /api/import/video-urls         → Accepts text file with URLs
```

**Frontend Changes:**
- Add "Import/Export" section to Settings page
- Export buttons trigger file downloads
- Import uses file upload inputs

**Pros:**
- Simpler frontend code
- Server handles validation and error reporting
- Consistent behavior across different clients
- Can batch process imports efficiently

**Cons:**
- More backend complexity
- Large imports may timeout (mitigated with async processing)

**Files to Modify:**
- Backend:
  - New: `backend/app/routers/import_export.py`
  - New: `backend/app/schemas/import_export.py`
  - Modify: `backend/app/main.py` (register new router)
- Frontend:
  - Modify: `frontend/src/pages/Settings.tsx`
  - New: `frontend/src/api/client.ts` (add import/export methods)
  - New: `frontend/src/components/settings/ImportExportSection.tsx`

---

#### Option B: Frontend-Driven Export, Server Import

**Description:** Export happens in browser using existing API data; import goes through server.

**Pros:**
- Simpler export implementation
- No new export endpoints needed

**Cons:**
- Export limited to what frontend already fetches
- Pagination issues with large datasets
- Less consistent architecture

---

### Recommended Approach

**Option A: Server-Side Only** is recommended for:
- Better scalability with large datasets
- Consistent architecture
- Proper validation and error handling
- Future extensibility (e.g., scheduled exports)

### JSON Schema Design

```json
{
  "version": "1.0",
  "exported_at": "2026-01-15T10:00:00Z",
  "channels": [
    {
      "youtube_channel_id": "UC...",
      "name": "Channel Name",
      "youtube_url": "https://youtube.com/channel/UC..."
    }
  ],
  "videos": [
    {
      "youtube_video_id": "abc123",
      "title": "Video Title",
      "video_url": "https://youtube.com/watch?v=abc123",
      "status": "saved",
      "saved_at": "2026-01-10T12:00:00Z"
    }
  ]
}
```

### Implementation Steps

1. Create Pydantic schemas for import/export data structures
2. Create import/export router with endpoints
3. Implement export logic (query DB, format JSON, return as download)
4. Implement import logic with validation and duplicate handling
5. Add bulk video URL import using existing `fetch_video_by_id`
6. Create frontend UI components for import/export actions
7. Add progress feedback for bulk imports
8. Write tests for import/export functionality

---

## Issue #5: Saved Videos View Modes

**Created:** 2026-01-14
**Priority:** Medium (UX enhancement)

### Requirements

1. **Big Thumbnail View** - Current default view
2. **Smaller Thumbnail View** - Compact grid with more items per row
3. **List View** - Horizontal layout with thumbnail, title, and info on one line
4. **Toggle between modes** with minimal refresh/re-render

### Current State Analysis

- `VideoList` component renders videos in a responsive grid (`grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4`)
- `VideoCard` component displays: thumbnail (large), title, channel name, published date, action buttons
- No view mode state management exists
- Saved page uses `useSavedVideos` hook with React Query

### Implementation Options

#### Option A: CSS-Only View Modes (Recommended)

**Description:** Use Tailwind classes to switch between layouts without changing component structure.

**Approach:**
- Add `viewMode` state to Saved page: `'large' | 'compact' | 'list'`
- Pass view mode to `VideoList` → applies different CSS classes
- Use `localStorage` to persist user preference

**View Mode Styles:**
```tsx
// Large (current)
grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6

// Compact
grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4

// List
flex flex-col gap-2
```

**Pros:**
- Minimal code changes
- Fast switching (no re-fetch)
- Uses existing components
- Easy to maintain

**Cons:**
- List view may need card layout adjustments
- Some duplication in styling logic

**Files to Modify:**
- Frontend:
  - Modify: `frontend/src/pages/Saved.tsx` (add view mode toggle)
  - Modify: `frontend/src/components/video/VideoList.tsx` (accept viewMode prop)
  - Modify: `frontend/src/components/video/VideoCard.tsx` (responsive to viewMode)
  - New: `frontend/src/components/common/ViewModeToggle.tsx`

---

#### Option B: Separate Card Components Per View

**Description:** Create `VideoCardLarge`, `VideoCardCompact`, `VideoCardList` components.

**Pros:**
- Cleaner separation of concerns
- Easier to customize each view independently

**Cons:**
- More code duplication
- Harder to maintain consistency
- More files to manage

---

### Recommended Approach

**Option A: CSS-Only View Modes** is recommended for:
- Faster implementation
- Less code duplication
- Easier maintenance
- Better performance (no component switching)

### UI Design

**View Mode Toggle:**
```
[≡ List] [⊞ Compact] [⊟ Large]
```
- Placed in the filter bar alongside channel/sort filters
- Active mode highlighted
- Preference persisted in localStorage

### VideoCard Adaptations by Mode

| Mode | Thumbnail | Title | Info | Actions |
|------|-----------|-------|------|---------|
| Large | 16:9 full width | Below thumb | Channel, date | Bottom |
| Compact | 16:9 smaller | Below thumb (truncated) | Date only | Hover |
| List | 120px fixed width | Inline right | Channel, date inline | Far right |

### Implementation Steps

1. Create `ViewModeToggle` component with icon buttons
2. Add `viewMode` state to Saved page with localStorage persistence
3. Pass `viewMode` prop to `VideoList` component
4. Update `VideoList` to apply different grid classes based on mode
5. Update `VideoCard` to render differently based on mode
6. Test responsiveness on all screen sizes
7. Consider adding view mode to Inbox page as well (optional)

---

## Issue #6: Inbox View Channel Separation

**Created:** 2026-01-14
**Priority:** Medium (UX enhancement)

### Requirements

1. View videos in inbox grouped by channel OR
2. Filter inbox videos by a specific channel
3. Make it easy to triage videos from one channel at a time

### Current State Analysis

- Inbox page fetches all inbox videos via `GET /api/videos/inbox`
- Videos are displayed in a single flat list sorted by `published_at desc`
- Each video already includes `channel_id` and `channel_name` in response
- No channel filtering on inbox endpoint (exists for saved videos)

### Implementation Options

#### Option A: Filter Dropdown (Similar to Saved Page)

**Description:** Add a channel filter dropdown to the Inbox page.

**Backend Changes:**
- Add optional `channel_id` query parameter to `/api/videos/inbox` endpoint

**Frontend Changes:**
- Add channel filter dropdown (reuse pattern from Saved page)
- Show "All Channels" as default option
- Bulk actions apply to filtered results

**Pros:**
- Consistent with Saved page UX
- Simple implementation
- Reuses existing patterns

**Cons:**
- User must manually switch between channels
- Doesn't show "at a glance" channel distribution

---

#### Option B: Grouped Channel Sections (Recommended)

**Description:** Display inbox videos grouped by channel with collapsible sections.

**UI Layout:**
```
Inbox (47 videos)
[Refresh] [Save All] [Discard All]

▼ Channel A (12 videos)
  [Video 1] [Video 2] [Video 3] ...
  [Save All for Channel] [Discard All for Channel]

▼ Channel B (8 videos)
  [Video 4] [Video 5] ...

► Channel C (27 videos) [collapsed]
```

**Frontend Changes:**
- Group videos by `channel_id` in frontend
- Collapsible sections per channel
- Per-channel bulk actions
- Optional: Sort channels by video count or alphabetically

**Backend Changes:**
- None required (all data already available)

**Pros:**
- Visual overview of all channels
- Easy per-channel triage
- Can collapse channels already reviewed
- No additional API calls

**Cons:**
- More complex UI
- Longer page if many channels with videos

---

#### Option C: Hybrid (Filter + Grouping)

**Description:** Combine filter dropdown with optional grouping toggle.

**Pros:**
- Maximum flexibility
- User can choose preferred workflow

**Cons:**
- More UI complexity
- May confuse users

---

### Recommended Approach

**Option B: Grouped Channel Sections** is recommended for:
- Better visual overview of inbox state
- Efficient per-channel triage workflow
- No backend changes required
- Clear organization

With an **optional filter dropdown** for users who prefer that workflow.

### Implementation Steps

1. Update `/api/videos/inbox` to accept optional `channel_id` filter parameter
2. Create `ChannelVideoGroup` component for collapsible sections
3. Group videos by channel in Inbox page
4. Add per-channel Save All / Discard All buttons
5. Add expand/collapse functionality with local state
6. Optionally add channel filter dropdown as alternative view
7. Persist user preference (grouped vs. flat) in localStorage
8. Test with many channels and edge cases (no videos, single channel)

### UI Components

**New Components:**
- `ChannelVideoGroup.tsx` - Collapsible section with header and video list
- `InboxViewToggle.tsx` - Toggle between grouped/flat view (optional)

**Modified Components:**
- `Inbox.tsx` - Add grouping logic and toggle

---

## Issue #7: Add YouTube Playlist Export

**Created:** 2026-01-14
**Priority:** Medium-Low (advanced feature)

### Requirements

#### Part 1: Play as Playlist (No API Required)
- Select up to 50 videos
- Generate a YouTube playlist URL and open in new tab
- Format: `https://www.youtube.com/watch_videos?video_ids=id1,id2,id3`

#### Part 2: Export to YouTube Playlist (API Required)
- Select up to 100 videos
- Add videos to an existing YouTube playlist via API
- Requires YouTube Data API v3 authentication

### Current State Analysis

- No video selection mechanism exists
- No YouTube API integration
- Videos have `youtube_video_id` field available
- Saved page already has bulk action patterns (but they're Save All/Discard All, not selective)

### Implementation Options

#### Option A: Play as Playlist Only (Recommended for MVP)

**Description:** Implement video selection and "Play as Playlist" feature without YouTube API.

**Frontend Changes:**
- Add checkbox selection to video cards
- Add selection controls (Select All, Clear, Count)
- Add "Play as Playlist" button (appears when videos selected)
- Generate and open YouTube watch_videos URL

**URL Format:**
```
https://www.youtube.com/watch_videos?video_ids=vid1,vid2,vid3,...
```

**Pros:**
- No API key required
- No authentication needed
- Simple implementation
- Works immediately

**Cons:**
- Limited to 50 videos (YouTube URL limit)
- Temporary playlist (not saved to user's YouTube account)

---

#### Option B: Full YouTube API Integration

**Description:** Implement OAuth2 flow and YouTube Data API integration.

**Backend Changes:**
- New: YouTube OAuth2 endpoints
- New: YouTube API service for playlist management
- Environment variables for Google OAuth credentials
- Token storage and refresh logic

**Frontend Changes:**
- Google Sign-In button
- Playlist selection UI
- Export progress indicator

**Required Setup:**
1. Google Cloud Console project
2. YouTube Data API v3 enabled
3. OAuth2 consent screen configured
4. Client ID and Client Secret

**Pros:**
- Full playlist management
- Videos added to real YouTube playlist
- Up to 100 videos at a time

**Cons:**
- Complex OAuth2 implementation
- Requires user to set up Google Cloud project
- API quota limits (10,000 units/day default)
- Privacy/security considerations

---

#### Option C: Phased Implementation (Recommended)

**Phase 1: Play as Playlist (No Auth)**
- Video selection UI
- Generate temporary playlist URL
- Open in YouTube

**Phase 2: YouTube API Export (Optional)**
- Configurable via Settings
- User provides their own API credentials
- OAuth2 flow for authentication
- Add to existing playlist feature

**Pros:**
- Immediate value from Phase 1
- Phase 2 optional for power users
- Lower barrier to entry

**Cons:**
- Two-phase implementation

---

### Recommended Approach

**Option C: Phased Implementation** is recommended:

**Phase 1 (Implement Now):**
- Add video selection UI
- "Play as Playlist" button for up to 50 videos
- No backend changes required

**Phase 2 (Future Enhancement):**
- YouTube API integration with OAuth2
- Export to real YouTube playlists
- Only for users who configure API credentials

### Implementation Steps (Phase 1)

1. Add selection state to video hooks or Saved page
2. Create `SelectableVideoCard` variant or add checkbox to existing
3. Add selection controls bar (appears when in selection mode)
4. Implement "Play as Playlist" button with URL generation
5. Add selection count display
6. Add keyboard shortcuts (optional): Shift+click for range select
7. Test URL generation with various video counts
8. Add clear visual feedback for selected videos

### UI Design

**Selection Mode:**
```
Saved Videos (23 videos)
[Enter Selection Mode] [Recently Deleted]

-- After entering selection mode --

12 selected                    [Cancel] [Play as Playlist ▶]

☑ Video 1    ☑ Video 2    ☐ Video 3    ☐ Video 4
☑ Video 5    ☐ Video 6    ☑ Video 7    ...
```

---

## Implementation Priority Recommendation

Based on dependencies and user value:

### Priority Order

1. **Issue #6: Inbox Channel Separation** (Quick Win)
   - No backend changes needed
   - Improves daily workflow significantly
   - Relatively simple frontend changes

2. **Issue #5: Saved Videos View Modes** (Quick Win)
   - No backend changes needed
   - Improves UX for users with many saved videos
   - CSS-focused implementation

3. **Issue #3: Import/Export Data** (Foundation)
   - Enables data portability
   - Important for backup/restore
   - More backend work but straightforward

4. **Issue #7: YouTube Playlist Export** (Phase 1 only)
   - Video selection UI is reusable
   - Play as Playlist provides immediate value
   - Phase 2 (API) can be deferred

---

## Summary

| Issue | Effort | Backend Changes | Frontend Changes | Dependencies |
|-------|--------|-----------------|------------------|--------------|
| #6 Inbox Separation | Low | Optional filter param | New grouping component | None |
| #5 View Modes | Low | None | View toggle, card variants | None |
| #3 Import/Export | Medium | New router + schemas | Settings section | None |
| #7 Playlist Export | Medium | None (Phase 1) | Selection UI | None |

All issues are independent and can be implemented in parallel by different developers if needed.
