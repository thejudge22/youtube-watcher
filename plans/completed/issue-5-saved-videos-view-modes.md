# Issue #5: Saved Videos View Modes - Development Plan

## Overview

Add multiple view modes to the Saved Videos page: Large Thumbnails (current default), Compact Grid, and List View. Users can toggle between modes with preferences persisted in localStorage.

**Priority:** High (Quick Win)
**Backend Changes:** None
**Frontend Changes:** View mode toggle + VideoCard/VideoList adaptations

---

## Current State

### Saved Page
**File:** `frontend/src/pages/Saved.tsx`

Current features:
- Channel filter dropdown
- Sort options (Published Date, Saved Date - Newest/Oldest)
- Recently Deleted modal
- Uses `useSavedVideos(params)` hook
- Renders via `VideoList` component

### VideoList Component
**File:** `frontend/src/components/video/VideoList.tsx`

Current layout:
```typescript
<div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
```

### VideoCard Component
**File:** `frontend/src/components/video/VideoCard.tsx`

Current structure:
- 16:9 aspect ratio thumbnail (full card width)
- Title below thumbnail (2-line clamp)
- Channel name
- Published date
- Saved date (if exists)
- Action buttons at bottom

---

## View Mode Specifications

### Mode 1: Large (Current Default)
- Grid: 1 → 2 → 3 → 4 columns (responsive)
- Gap: 24px (gap-6)
- Thumbnail: Full width, 16:9 aspect ratio
- Title: Below thumbnail, 2 lines max
- Info: Channel name, published date, saved date
- Actions: Full buttons at bottom

### Mode 2: Compact
- Grid: 2 → 3 → 4 → 6 columns (responsive)
- Gap: 16px (gap-4)
- Thumbnail: Full width, 16:9 aspect ratio (smaller due to column count)
- Title: Below thumbnail, 1 line only
- Info: Published date only
- Actions: Show on hover

### Mode 3: List
- Layout: Flex column, no grid
- Gap: 8px (gap-2)
- Thumbnail: 160px fixed width, left side
- Title: Right of thumbnail, single line
- Info: Channel, published date, saved date - inline
- Actions: Far right, always visible

---

## Implementation Tasks

### Task 1: Create ViewModeToggle Component

**File to create:** `frontend/src/components/common/ViewModeToggle.tsx`

**Implementation:**

```typescript
import { Squares2X2Icon, ListBulletIcon, RectangleStackIcon } from '@heroicons/react/24/outline';

export type ViewMode = 'large' | 'compact' | 'list';

interface ViewModeToggleProps {
  viewMode: ViewMode;
  onChange: (mode: ViewMode) => void;
}

const modes: { value: ViewMode; icon: typeof Squares2X2Icon; label: string }[] = [
  { value: 'list', icon: ListBulletIcon, label: 'List' },
  { value: 'compact', icon: Squares2X2Icon, label: 'Compact' },
  { value: 'large', icon: RectangleStackIcon, label: 'Large' },
];

export default function ViewModeToggle({ viewMode, onChange }: ViewModeToggleProps) {
  return (
    <div className="flex rounded-lg overflow-hidden border border-gray-600">
      {modes.map(({ value, icon: Icon, label }) => (
        <button
          key={value}
          onClick={() => onChange(value)}
          className={`flex items-center gap-1 px-3 py-1.5 text-sm transition-colors ${
            viewMode === value
              ? 'bg-gray-600 text-white'
              : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
          }`}
          title={`${label} view`}
        >
          <Icon className="w-4 h-4" />
          <span className="hidden sm:inline">{label}</span>
        </button>
      ))}
    </div>
  );
}
```

---

### Task 2: Create useLocalStorage Hook (Utility)

**File to create:** `frontend/src/hooks/useLocalStorage.ts`

**Purpose:** Reusable hook for persisting state to localStorage.

**Implementation:**

```typescript
import { useState, useEffect } from 'react';

export function useLocalStorage<T>(key: string, defaultValue: T): [T, (value: T) => void] {
  const [value, setValue] = useState<T>(() => {
    try {
      const saved = localStorage.getItem(key);
      return saved ? JSON.parse(saved) : defaultValue;
    } catch {
      return defaultValue;
    }
  });

  useEffect(() => {
    try {
      localStorage.setItem(key, JSON.stringify(value));
    } catch {
      // Ignore localStorage errors
    }
  }, [key, value]);

  return [value, setValue];
}
```

---

### Task 3: Update VideoList Component

**File to modify:** `frontend/src/components/video/VideoList.tsx`

**Changes:**
1. Accept `viewMode` prop
2. Apply different grid/flex classes based on mode
3. Pass `viewMode` to each VideoCard

**Current code structure:**
```typescript
interface VideoListProps {
  videos: Video[];
  onSave?: (id: string) => void;
  onDiscard: (id: string) => void;
  emptyMessage?: string;
  showSaveButton?: boolean;
  showDiscardButton?: boolean;
}
```

**Updated implementation:**

```typescript
import { ViewMode } from './ViewModeToggle';

interface VideoListProps {
  videos: Video[];
  onSave?: (id: string) => void;
  onDiscard: (id: string) => void;
  emptyMessage?: string;
  showSaveButton?: boolean;
  showDiscardButton?: boolean;
  viewMode?: ViewMode;
}

export default function VideoList({
  videos,
  onSave,
  onDiscard,
  emptyMessage = 'No videos found',
  showSaveButton = true,
  showDiscardButton = true,
  viewMode = 'large',
}: VideoListProps) {
  if (videos.length === 0) {
    return (
      <div className="text-center py-12 text-gray-400">
        {emptyMessage}
      </div>
    );
  }

  const containerClasses = {
    large: 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6',
    compact: 'grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4',
    list: 'flex flex-col gap-2',
  };

  return (
    <div className={containerClasses[viewMode]}>
      {videos.map((video) => (
        <VideoCard
          key={video.id}
          video={video}
          onSave={showSaveButton && onSave ? () => onSave(video.id) : undefined}
          onDiscard={showDiscardButton ? () => onDiscard(video.id) : undefined}
          viewMode={viewMode}
        />
      ))}
    </div>
  );
}
```

---

### Task 4: Update VideoCard Component

**File to modify:** `frontend/src/components/video/VideoCard.tsx`

**Changes:**
1. Accept `viewMode` prop
2. Render different layouts based on mode
3. Adjust thumbnail sizing, text truncation, and button visibility

**Implementation approach:**

Add viewMode prop to the interface:
```typescript
import { ViewMode } from '../common/ViewModeToggle';

interface VideoCardProps {
  video: Video;
  onSave?: () => void;
  onDiscard?: () => void;
  viewMode?: ViewMode;
}
```

Update the component to render conditionally:

```typescript
export default function VideoCard({
  video,
  onSave,
  onDiscard,
  viewMode = 'large',
}: VideoCardProps) {
  const [isHovered, setIsHovered] = useState(false);

  // Format dates
  const publishedDate = formatDate(video.published_at);
  const savedDate = video.saved_at ? formatDateTime(video.saved_at) : null;

  // List view - horizontal layout
  if (viewMode === 'list') {
    return (
      <div className="flex items-center gap-4 p-2 bg-gray-800 rounded-lg hover:bg-gray-750 transition-colors">
        {/* Thumbnail - fixed width */}
        <a
          href={video.video_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-shrink-0 w-40"
        >
          <div className="aspect-video rounded overflow-hidden">
            <img
              src={video.thumbnail_url}
              alt={video.title}
              className="w-full h-full object-cover"
            />
          </div>
        </a>

        {/* Content - flexible */}
        <div className="flex-1 min-w-0">
          <a
            href={video.video_url}
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-white hover:text-blue-400 line-clamp-1"
          >
            {video.title}
          </a>
          <div className="text-sm text-gray-400 mt-1">
            <span>{video.channel_name}</span>
            <span className="mx-2">•</span>
            <span>{publishedDate}</span>
            {savedDate && (
              <>
                <span className="mx-2">•</span>
                <span>Saved {savedDate}</span>
              </>
            )}
          </div>
        </div>

        {/* Actions - fixed right */}
        <div className="flex-shrink-0 flex gap-2">
          {onSave && (
            <button
              onClick={onSave}
              className="px-3 py-1 text-sm bg-blue-600 hover:bg-blue-700 rounded transition-colors"
            >
              Save
            </button>
          )}
          {onDiscard && (
            <button
              onClick={onDiscard}
              className="px-3 py-1 text-sm bg-gray-600 hover:bg-gray-500 rounded transition-colors"
            >
              {video.status === 'saved' ? 'Remove' : 'Discard'}
            </button>
          )}
        </div>
      </div>
    );
  }

  // Compact view - smaller cards with hover actions
  if (viewMode === 'compact') {
    return (
      <div
        className="bg-gray-800 rounded-lg overflow-hidden hover:bg-gray-750 transition-colors relative"
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      >
        {/* Thumbnail */}
        <a
          href={video.video_url}
          target="_blank"
          rel="noopener noreferrer"
        >
          <div className="aspect-video">
            <img
              src={video.thumbnail_url}
              alt={video.title}
              className="w-full h-full object-cover"
            />
          </div>
        </a>

        {/* Content */}
        <div className="p-2">
          <a
            href={video.video_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm font-medium text-white hover:text-blue-400 line-clamp-1"
          >
            {video.title}
          </a>
          <div className="text-xs text-gray-400 mt-1">
            {publishedDate}
          </div>
        </div>

        {/* Hover actions overlay */}
        {isHovered && (onSave || onDiscard) && (
          <div className="absolute inset-0 bg-black/60 flex items-center justify-center gap-2">
            {onSave && (
              <button
                onClick={onSave}
                className="px-3 py-1 text-sm bg-blue-600 hover:bg-blue-700 rounded transition-colors"
              >
                Save
              </button>
            )}
            {onDiscard && (
              <button
                onClick={onDiscard}
                className="px-3 py-1 text-sm bg-gray-600 hover:bg-gray-500 rounded transition-colors"
              >
                {video.status === 'saved' ? 'Remove' : 'Discard'}
              </button>
            )}
          </div>
        )}
      </div>
    );
  }

  // Large view (default) - original layout
  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden hover:bg-gray-750 transition-colors">
      {/* Thumbnail */}
      <a
        href={video.video_url}
        target="_blank"
        rel="noopener noreferrer"
      >
        <div className="aspect-video">
          <img
            src={video.thumbnail_url}
            alt={video.title}
            className="w-full h-full object-cover"
          />
        </div>
      </a>

      {/* Content */}
      <div className="p-4">
        <a
          href={video.video_url}
          target="_blank"
          rel="noopener noreferrer"
          className="font-medium text-white hover:text-blue-400 line-clamp-2"
        >
          {video.title}
        </a>
        <div className="text-sm text-gray-400 mt-2">
          <div>{video.channel_name}</div>
          <div className="mt-1">{publishedDate}</div>
          {savedDate && (
            <div className="mt-1 text-xs">Saved {savedDate}</div>
          )}
        </div>

        {/* Actions */}
        {(onSave || onDiscard) && (
          <div className="flex gap-2 mt-4">
            {onSave && (
              <button
                onClick={onSave}
                className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded transition-colors"
              >
                Save
              </button>
            )}
            {onDiscard && (
              <button
                onClick={onDiscard}
                className="flex-1 px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded transition-colors"
              >
                {video.status === 'saved' ? 'Remove' : 'Discard'}
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
```

**Note:** The exact styling should match the existing VideoCard. Review the current implementation and adjust classes accordingly.

---

### Task 5: Update Saved Page

**File to modify:** `frontend/src/pages/Saved.tsx`

**Changes:**
1. Import ViewModeToggle and useLocalStorage
2. Add view mode state with localStorage persistence
3. Add ViewModeToggle to the filter bar
4. Pass viewMode to VideoList

**Implementation:**

Add imports:
```typescript
import ViewModeToggle, { ViewMode } from '../components/common/ViewModeToggle';
import { useLocalStorage } from '../hooks/useLocalStorage';
```

Add view mode state:
```typescript
const [viewMode, setViewMode] = useLocalStorage<ViewMode>('saved-view-mode', 'large');
```

Add ViewModeToggle to the filter bar (alongside existing channel/sort filters):
```typescript
<div className="flex flex-wrap items-center gap-4 mb-6">
  {/* Existing channel filter dropdown */}
  <select ...>
    ...
  </select>

  {/* Existing sort filter dropdown */}
  <select ...>
    ...
  </select>

  {/* Add view mode toggle */}
  <ViewModeToggle viewMode={viewMode} onChange={setViewMode} />

  {/* Recently Deleted button */}
  <button ...>
    Recently Deleted
  </button>
</div>
```

Update VideoList to include viewMode:
```typescript
<VideoList
  videos={videos || []}
  onDiscard={handleDiscard}
  showSaveButton={false}
  emptyMessage="No saved videos"
  viewMode={viewMode}
/>
```

---

### Task 6: Optional - Add View Modes to Inbox Page

**File to modify:** `frontend/src/pages/Inbox.tsx`

If desired, the same view mode toggle can be added to the Inbox page. Use the same pattern:

```typescript
const [viewMode, setViewMode] = useLocalStorage<ViewMode>('inbox-video-view-mode', 'large');
```

Add ViewModeToggle to the header and pass viewMode to VideoList components.

**Note:** This is optional and can be done as a follow-up.

---

## File Summary

### Files to Create
1. `frontend/src/components/common/ViewModeToggle.tsx`
2. `frontend/src/hooks/useLocalStorage.ts`

### Files to Modify
1. `frontend/src/components/video/VideoList.tsx` - Add viewMode prop
2. `frontend/src/components/video/VideoCard.tsx` - Render different layouts per mode
3. `frontend/src/pages/Saved.tsx` - Add view mode toggle

### Optional Files to Modify
4. `frontend/src/pages/Inbox.tsx` - Add view mode toggle (follow-up)

---

## Styling Reference

### Tailwind Classes by View Mode

| Element | Large | Compact | List |
|---------|-------|---------|------|
| Container | `grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6` | `grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4` | `flex flex-col gap-2` |
| Card | `rounded-lg overflow-hidden` | `rounded-lg overflow-hidden relative` | `flex items-center gap-4 p-2 rounded-lg` |
| Thumbnail | `aspect-video` (full width) | `aspect-video` (full width, smaller) | `w-40 flex-shrink-0` |
| Title | `line-clamp-2 font-medium` | `line-clamp-1 text-sm font-medium` | `line-clamp-1 font-medium` |
| Info | Multiple lines | Single line, date only | Inline with dots |
| Actions | Full buttons below | Hover overlay | Inline right |

---

## Testing Checklist

- [ ] ViewModeToggle renders with three mode buttons
- [ ] Clicking mode buttons switches the active mode
- [ ] Active mode is visually highlighted
- [ ] View mode persists in localStorage across refreshes
- [ ] Large view matches current default layout
- [ ] Compact view shows more videos per row
- [ ] Compact view shows actions on hover
- [ ] List view shows horizontal layout
- [ ] List view has fixed thumbnail width
- [ ] All view modes display correctly on mobile
- [ ] All view modes display correctly on tablet
- [ ] All view modes display correctly on desktop
- [ ] Video actions work correctly in all modes
- [ ] Empty state displays correctly in all modes
- [ ] Loading state displays correctly

---

## Dependencies

- `@heroicons/react` - Already installed
- No new npm packages required

---

## Notes

- The compact view uses a hover overlay for actions to maintain a clean grid appearance
- The list view is designed for quick scanning of many videos
- Consider adding keyboard navigation for accessibility (future enhancement)
- The ViewModeToggle component can be reused on the Inbox page
- The useLocalStorage hook is a reusable utility for other settings
