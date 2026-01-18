# Issue #7: YouTube Playlist Export (Phase 1) - Development Plan

> **Status:** ✅ Completed (v1.5.0)
> **Completion Date:** January 18, 2026

## Overview

Add video selection functionality and "Play as Playlist" feature that generates a YouTube watch_videos URL to play selected videos as a temporary playlist.

**Priority:** Medium
**Backend Changes:** None (Phase 1)
**Frontend Changes:** Selection UI + playlist URL generation

**Note:** This plan covers Phase 1 only (no YouTube API integration). Phase 2 (OAuth + YouTube Playlist API) can be implemented as a future enhancement.

---

## Current State

### Saved Page
**File:** `frontend/src/pages/Saved.tsx`

Current features:
- Video list display
- Channel filter
- Sort options
- No selection mechanism
- No bulk action selection (only "Save All" type actions)

### VideoCard Component
**File:** `frontend/src/components/video/VideoCard.tsx`

Current structure:
- Displays video thumbnail, title, channel, dates
- Action buttons (Save/Discard/Remove)
- No checkbox or selection indicator

### Video Type
**File:** `frontend/src/types/index.ts`

```typescript
interface Video {
  id: string;
  youtube_video_id: string;
  // ... other fields
}
```

The `youtube_video_id` field is what we need for generating the playlist URL.

---

## YouTube Playlist URL Format

YouTube supports a temporary playlist URL format:
```
https://www.youtube.com/watch_videos?video_ids=id1,id2,id3,...
```

**Limitations:**
- Maximum ~50 videos (URL length limits)
- Playlist is temporary (not saved to user's account)
- Videos play in the order specified

---

## Implementation Tasks

### Task 1: Create Selection Context/Hook

**File to create:** `frontend/src/hooks/useVideoSelection.ts`

**Purpose:** Manage selected video state across components.

**Implementation:**

```typescript
import { useState, useCallback, useMemo } from 'react';
import { Video } from '../types';

export interface VideoSelectionState {
  selectedIds: Set<string>;
  isSelectionMode: boolean;
  selectedCount: number;
}

export interface VideoSelectionActions {
  enterSelectionMode: () => void;
  exitSelectionMode: () => void;
  toggleSelection: (videoId: string) => void;
  selectAll: (videos: Video[]) => void;
  clearSelection: () => void;
  isSelected: (videoId: string) => boolean;
  getSelectedVideos: (videos: Video[]) => Video[];
}

export function useVideoSelection(): VideoSelectionState & VideoSelectionActions {
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [isSelectionMode, setIsSelectionMode] = useState(false);

  const enterSelectionMode = useCallback(() => {
    setIsSelectionMode(true);
  }, []);

  const exitSelectionMode = useCallback(() => {
    setIsSelectionMode(false);
    setSelectedIds(new Set());
  }, []);

  const toggleSelection = useCallback((videoId: string) => {
    setSelectedIds(prev => {
      const next = new Set(prev);
      if (next.has(videoId)) {
        next.delete(videoId);
      } else {
        next.add(videoId);
      }
      return next;
    });
  }, []);

  const selectAll = useCallback((videos: Video[]) => {
    // Limit to 50 for playlist URL limit
    const idsToSelect = videos.slice(0, 50).map(v => v.id);
    setSelectedIds(new Set(idsToSelect));
  }, []);

  const clearSelection = useCallback(() => {
    setSelectedIds(new Set());
  }, []);

  const isSelected = useCallback((videoId: string) => {
    return selectedIds.has(videoId);
  }, [selectedIds]);

  const getSelectedVideos = useCallback((videos: Video[]) => {
    return videos.filter(v => selectedIds.has(v.id));
  }, [selectedIds]);

  const selectedCount = useMemo(() => selectedIds.size, [selectedIds]);

  return {
    selectedIds,
    isSelectionMode,
    selectedCount,
    enterSelectionMode,
    exitSelectionMode,
    toggleSelection,
    selectAll,
    clearSelection,
    isSelected,
    getSelectedVideos,
  };
}
```

---

### Task 2: Create Playlist URL Generator Utility

**File to create:** `frontend/src/utils/playlist.ts`

**Purpose:** Generate YouTube playlist URLs from selected videos.

**Implementation:**

```typescript
import { Video } from '../types';

const MAX_PLAYLIST_VIDEOS = 50;
const YOUTUBE_WATCH_VIDEOS_URL = 'https://www.youtube.com/watch_videos';

export interface PlaylistResult {
  url: string;
  videoCount: number;
  truncated: boolean;
}

/**
 * Generates a YouTube playlist URL from an array of videos.
 * YouTube's watch_videos endpoint supports up to ~50 videos.
 */
export function generatePlaylistUrl(videos: Video[]): PlaylistResult {
  const truncated = videos.length > MAX_PLAYLIST_VIDEOS;
  const videosToInclude = videos.slice(0, MAX_PLAYLIST_VIDEOS);

  const videoIds = videosToInclude.map(v => v.youtube_video_id).join(',');
  const url = `${YOUTUBE_WATCH_VIDEOS_URL}?video_ids=${videoIds}`;

  return {
    url,
    videoCount: videosToInclude.length,
    truncated,
  };
}

/**
 * Opens the playlist URL in a new tab.
 */
export function openPlaylist(videos: Video[]): PlaylistResult {
  const result = generatePlaylistUrl(videos);
  window.open(result.url, '_blank', 'noopener,noreferrer');
  return result;
}
```

---

### Task 3: Create SelectionBar Component

**File to create:** `frontend/src/components/video/SelectionBar.tsx`

**Purpose:** Floating/sticky bar that appears when in selection mode, showing count and actions.

**Implementation:**

```typescript
import { XMarkIcon, PlayIcon } from '@heroicons/react/24/outline';
import Button from '../common/Button';

interface SelectionBarProps {
  selectedCount: number;
  totalCount: number;
  onSelectAll: () => void;
  onClearSelection: () => void;
  onCancel: () => void;
  onPlayAsPlaylist: () => void;
  maxPlaylistSize?: number;
}

export default function SelectionBar({
  selectedCount,
  totalCount,
  onSelectAll,
  onClearSelection,
  onCancel,
  onPlayAsPlaylist,
  maxPlaylistSize = 50,
}: SelectionBarProps) {
  const canPlay = selectedCount > 0;
  const isAtLimit = selectedCount >= maxPlaylistSize;

  return (
    <div className="sticky top-0 z-10 bg-gray-800 border-b border-gray-700 p-4 -mx-4 mb-4">
      <div className="flex items-center justify-between gap-4">
        {/* Left side - Selection info */}
        <div className="flex items-center gap-4">
          <button
            onClick={onCancel}
            className="p-1 hover:bg-gray-700 rounded transition-colors"
            title="Exit selection mode"
          >
            <XMarkIcon className="w-5 h-5 text-gray-400" />
          </button>

          <span className="text-white font-medium">
            {selectedCount} selected
            {isAtLimit && (
              <span className="text-yellow-400 ml-2 text-sm">
                (max {maxPlaylistSize})
              </span>
            )}
          </span>

          <div className="flex gap-2">
            <button
              onClick={onSelectAll}
              className="text-sm text-blue-400 hover:text-blue-300"
              disabled={selectedCount === Math.min(totalCount, maxPlaylistSize)}
            >
              Select All (up to {maxPlaylistSize})
            </button>
            <span className="text-gray-600">|</span>
            <button
              onClick={onClearSelection}
              className="text-sm text-gray-400 hover:text-gray-300"
              disabled={selectedCount === 0}
            >
              Clear
            </button>
          </div>
        </div>

        {/* Right side - Actions */}
        <div className="flex items-center gap-2">
          <Button
            variant="primary"
            onClick={onPlayAsPlaylist}
            disabled={!canPlay}
          >
            <PlayIcon className="w-4 h-4 mr-2" />
            Play as Playlist
          </Button>
        </div>
      </div>
    </div>
  );
}
```

---

### Task 4: Create SelectableVideoCard Component (or Update VideoCard)

**Option A: Add selection props to existing VideoCard**

**File to modify:** `frontend/src/components/video/VideoCard.tsx`

**Changes:**
1. Add optional selection props
2. Show checkbox when in selection mode
3. Add click handler for selection toggle

Add to the interface:
```typescript
interface VideoCardProps {
  video: Video;
  onSave?: () => void;
  onDiscard?: () => void;
  viewMode?: ViewMode;
  // New selection props
  selectable?: boolean;
  selected?: boolean;
  onToggleSelect?: () => void;
}
```

Update the component to handle selection:

```typescript
export default function VideoCard({
  video,
  onSave,
  onDiscard,
  viewMode = 'large',
  selectable = false,
  selected = false,
  onToggleSelect,
}: VideoCardProps) {
  // ... existing code ...

  // Handle card click in selection mode
  const handleCardClick = (e: React.MouseEvent) => {
    if (selectable && onToggleSelect) {
      // Prevent click if clicking on a link or button
      if ((e.target as HTMLElement).closest('a, button')) {
        return;
      }
      onToggleSelect();
    }
  };

  // For Large view, add checkbox and selection styling
  if (viewMode === 'large' || !viewMode) {
    return (
      <div
        className={`bg-gray-800 rounded-lg overflow-hidden transition-colors ${
          selectable ? 'cursor-pointer' : ''
        } ${
          selected ? 'ring-2 ring-blue-500 bg-gray-750' : 'hover:bg-gray-750'
        }`}
        onClick={handleCardClick}
      >
        {/* Selection checkbox overlay */}
        {selectable && (
          <div className="absolute top-2 left-2 z-10">
            <div
              className={`w-6 h-6 rounded border-2 flex items-center justify-center transition-colors ${
                selected
                  ? 'bg-blue-500 border-blue-500'
                  : 'bg-gray-900/70 border-gray-400 hover:border-white'
              }`}
            >
              {selected && (
                <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path
                    fillRule="evenodd"
                    d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                    clipRule="evenodd"
                  />
                </svg>
              )}
            </div>
          </div>
        )}

        {/* Thumbnail - make relative for checkbox positioning */}
        <div className="relative">
          <a
            href={video.video_url}
            target="_blank"
            rel="noopener noreferrer"
            onClick={(e) => selectable && e.preventDefault()}
          >
            <div className="aspect-video">
              <img
                src={video.thumbnail_url}
                alt={video.title}
                className="w-full h-full object-cover"
              />
            </div>
          </a>

          {/* Selection checkbox - positioned in thumbnail corner */}
          {selectable && (
            <div className="absolute top-2 left-2">
              <div
                className={`w-6 h-6 rounded border-2 flex items-center justify-center transition-colors ${
                  selected
                    ? 'bg-blue-500 border-blue-500'
                    : 'bg-gray-900/70 border-gray-400'
                }`}
              >
                {selected && (
                  <svg className="w-4 h-4 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Rest of the card content... */}
        {/* ... existing content ... */}
      </div>
    );
  }

  // ... compact and list views with similar selection additions ...
}
```

---

### Task 5: Update VideoList to Support Selection

**File to modify:** `frontend/src/components/video/VideoList.tsx`

**Changes:**
1. Add selection props
2. Pass selection state to each VideoCard

Update the interface:
```typescript
interface VideoListProps {
  videos: Video[];
  onSave?: (id: string) => void;
  onDiscard: (id: string) => void;
  emptyMessage?: string;
  showSaveButton?: boolean;
  showDiscardButton?: boolean;
  viewMode?: ViewMode;
  // New selection props
  selectable?: boolean;
  selectedIds?: Set<string>;
  onToggleSelect?: (id: string) => void;
}
```

Update the VideoCard rendering:
```typescript
{videos.map((video) => (
  <VideoCard
    key={video.id}
    video={video}
    onSave={showSaveButton && onSave ? () => onSave(video.id) : undefined}
    onDiscard={showDiscardButton ? () => onDiscard(video.id) : undefined}
    viewMode={viewMode}
    selectable={selectable}
    selected={selectedIds?.has(video.id) ?? false}
    onToggleSelect={onToggleSelect ? () => onToggleSelect(video.id) : undefined}
  />
))}
```

---

### Task 6: Update Saved Page with Selection Mode

**File to modify:** `frontend/src/pages/Saved.tsx`

**Changes:**
1. Import selection hook and components
2. Add "Select" button to enter selection mode
3. Show SelectionBar when in selection mode
4. Pass selection props to VideoList
5. Implement Play as Playlist action

**Implementation:**

Add imports:
```typescript
import { useVideoSelection } from '../hooks/useVideoSelection';
import SelectionBar from '../components/video/SelectionBar';
import { openPlaylist } from '../utils/playlist';
```

Add selection hook usage:
```typescript
const {
  isSelectionMode,
  selectedCount,
  enterSelectionMode,
  exitSelectionMode,
  toggleSelection,
  selectAll,
  clearSelection,
  isSelected,
  getSelectedVideos,
  selectedIds,
} = useVideoSelection();
```

Add Play as Playlist handler:
```typescript
const handlePlayAsPlaylist = () => {
  if (!videos) return;

  const selectedVideos = getSelectedVideos(videos);
  const result = openPlaylist(selectedVideos);

  if (result.truncated) {
    // Optionally show a toast/notification that some videos were truncated
    console.log(`Playlist opened with ${result.videoCount} videos (some were truncated)`);
  }

  // Optionally exit selection mode after playing
  exitSelectionMode();
};
```

Update the JSX:

```typescript
return (
  <div className="px-4">
    {/* Header */}
    <div className="flex items-center justify-between mb-6">
      <h1 className="text-2xl font-bold">
        Saved {videos && videos.length > 0 && `(${videos.length} videos)`}
      </h1>

      {!isSelectionMode ? (
        <div className="flex items-center gap-4">
          {/* Existing filters */}
          {/* ... channel filter, sort filter, view mode toggle ... */}

          {/* Select button */}
          {videos && videos.length > 0 && (
            <Button
              variant="secondary"
              onClick={enterSelectionMode}
            >
              Select
            </Button>
          )}

          {/* Recently Deleted button */}
          {/* ... */}
        </div>
      ) : null}
    </div>

    {/* Selection Bar - shown when in selection mode */}
    {isSelectionMode && (
      <SelectionBar
        selectedCount={selectedCount}
        totalCount={videos?.length || 0}
        onSelectAll={() => videos && selectAll(videos)}
        onClearSelection={clearSelection}
        onCancel={exitSelectionMode}
        onPlayAsPlaylist={handlePlayAsPlaylist}
      />
    )}

    {/* Filters - hide when in selection mode for cleaner UI */}
    {!isSelectionMode && (
      <div className="flex flex-wrap items-center gap-4 mb-6">
        {/* ... existing filters ... */}
      </div>
    )}

    {/* Video List */}
    <VideoList
      videos={videos || []}
      onDiscard={handleDiscard}
      showSaveButton={false}
      emptyMessage="No saved videos"
      viewMode={viewMode}
      selectable={isSelectionMode}
      selectedIds={selectedIds}
      onToggleSelect={toggleSelection}
    />
  </div>
);
```

---

### Task 7: Add Visual Feedback for Playlist Opening

**Optional enhancement:** Show a toast notification when playlist opens.

If a toast system exists, use it. Otherwise, add a simple notification:

```typescript
const [notification, setNotification] = useState<string | null>(null);

const handlePlayAsPlaylist = () => {
  if (!videos) return;

  const selectedVideos = getSelectedVideos(videos);
  const result = openPlaylist(selectedVideos);

  if (result.truncated) {
    setNotification(`Opened playlist with ${result.videoCount} videos (max 50)`);
  } else {
    setNotification(`Opened playlist with ${result.videoCount} videos`);
  }

  // Clear notification after 3 seconds
  setTimeout(() => setNotification(null), 3000);

  exitSelectionMode();
};

// In JSX, add notification display:
{notification && (
  <div className="fixed bottom-4 right-4 bg-gray-800 border border-gray-600 rounded-lg px-4 py-2 shadow-lg">
    {notification}
  </div>
)}
```

---

## File Summary

### Files to Create
1. `frontend/src/hooks/useVideoSelection.ts` - Selection state management
2. `frontend/src/utils/playlist.ts` - Playlist URL generation
3. `frontend/src/components/video/SelectionBar.tsx` - Selection mode UI

### Files to Modify
1. `frontend/src/components/video/VideoCard.tsx` - Add selection props and checkbox
2. `frontend/src/components/video/VideoList.tsx` - Pass selection props to cards
3. `frontend/src/pages/Saved.tsx` - Add selection mode and playlist action

---

## UI Workflow

### Entering Selection Mode
1. User clicks "Select" button in the header
2. Header filters are hidden
3. SelectionBar appears (sticky at top)
4. Video cards show checkboxes

### Selecting Videos
1. User clicks on video cards to toggle selection
2. Checkbox shows selected state
3. Card has blue ring when selected
4. SelectionBar shows current count
5. "Select All" selects up to 50 videos
6. "Clear" removes all selections

### Playing as Playlist
1. User clicks "Play as Playlist" button
2. YouTube opens in new tab with playlist URL
3. Selection mode exits automatically
4. Notification shows video count

### Exiting Selection Mode
1. User clicks X button in SelectionBar
2. Or clicks "Cancel"
3. Selection cleared
4. Normal view restored

---

## Testing Checklist

### Selection Mode
- [ ] "Select" button appears when videos exist
- [ ] Clicking "Select" enters selection mode
- [ ] Header filters are hidden in selection mode
- [ ] SelectionBar appears at top
- [ ] Clicking X exits selection mode
- [ ] Exiting clears all selections

### Video Selection
- [ ] Clicking video card toggles selection
- [ ] Checkbox appears on video cards
- [ ] Selected cards have visual indicator (ring)
- [ ] Selected count updates correctly
- [ ] "Select All" selects up to 50 videos
- [ ] "Clear" removes all selections
- [ ] Can select videos in all view modes (large, compact, list)

### Play as Playlist
- [ ] Button is disabled when no videos selected
- [ ] Button is enabled when videos selected
- [ ] Clicking opens YouTube in new tab
- [ ] URL contains correct video IDs
- [ ] URL is in correct format (watch_videos?video_ids=...)
- [ ] Selection mode exits after playing
- [ ] Works with 1 video
- [ ] Works with 50 videos
- [ ] Truncates at 50 videos if more selected

### Edge Cases
- [ ] Works with empty video list (Select button hidden)
- [ ] Works when filtered by channel
- [ ] Works with different sort orders
- [ ] Keyboard accessibility (optional)

---

## Dependencies

- `@heroicons/react` - Already installed
- No new npm packages required

---

## Future Enhancements (Phase 2)

Phase 2 would add YouTube API integration:

1. **Settings page additions:**
   - Google OAuth configuration
   - Client ID/Secret fields
   - Connect/Disconnect YouTube account

2. **Backend additions:**
   - OAuth2 endpoints (`/api/youtube/auth`, `/api/youtube/callback`)
   - Token storage in database or environment
   - YouTube Data API service for playlist management

3. **Frontend additions:**
   - "Add to Playlist" action in SelectionBar
   - Playlist selector modal
   - Create new playlist option
   - Progress indicator for adding videos

4. **Requirements:**
   - Google Cloud Console project
   - YouTube Data API v3 enabled
   - OAuth2 consent screen configured
   - User provides their own API credentials

This is out of scope for Phase 1 and can be implemented as a separate issue.

---

## Notes

- The `watch_videos` URL format is unofficial but widely used and reliable
- Maximum 50 videos is a practical limit due to URL length
- Selection is limited to videos currently displayed (doesn't persist across filter changes)
- Consider adding keyboard shortcuts (Shift+click for range select) as a future enhancement
- The selection hook is reusable and could be applied to Inbox page if desired

---

## Implementation Summary

**Completed:** v1.5.0

### What Was Implemented

The selection UI infrastructure was already in place from the v1.4.0 release (selection mode, checkboxes, bulk remove). This release added the playlist generation capability:

1. **Created `frontend/src/utils/playlist.ts`**
   - `generatePlaylistUrl()` - Generates YouTube watch_videos URL from video array
   - `openPlaylist()` - Opens playlist in new tab
   - Supports up to 50 videos (URL length limit)

2. **Updated `frontend/src/pages/Saved.tsx`**
   - Added `handlePlayAsPlaylist()` function
   - Added "Play as Playlist" button to selection toolbar
   - Button disabled when no videos selected
   - Exits selection mode after opening playlist

### Files Changed
- `frontend/src/utils/playlist.ts` (created)
- `frontend/src/pages/Saved.tsx` (modified)

### Not Implemented (Out of Scope)
- `useVideoSelection` hook - Selection logic was already implemented inline in Saved.tsx
- `SelectionBar` component - Selection toolbar was already built inline in Saved.tsx
- VideoCard/VideoList selection props - Already implemented in v1.4.0
