# Issue #6: Inbox View Channel Separation - Development Plan

## Overview

Add the ability to view inbox videos grouped by channel with collapsible sections, making it easier to triage videos from one channel at a time.

**Priority:** High (Quick Win)
**Backend Changes:** Optional filter parameter
**Frontend Changes:** New grouping component + UI updates

---

## Current State

### Backend Endpoint
**File:** `backend/app/routers/videos.py`

The inbox endpoint currently fetches all inbox videos without channel filtering:

```python
@router.get("/inbox", response_model=list[VideoResponse])
async def get_inbox_videos(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
```

### Frontend Page
**File:** `frontend/src/pages/Inbox.tsx`

Current implementation:
- Uses `useInboxVideos()` hook to fetch all inbox videos
- Renders videos in a flat list via `VideoList` component
- Has bulk actions: Save All, Discard All, Refresh
- No grouping or filtering by channel

### Related Files
- `frontend/src/hooks/useVideos.ts` - Contains `useInboxVideos()` hook
- `frontend/src/api/client.ts` - Contains `videosApi.getInbox()`
- `frontend/src/components/video/VideoList.tsx` - Renders video grid
- `frontend/src/components/video/VideoCard.tsx` - Individual video card

---

## Implementation Tasks

### Task 1: Backend - Add Optional Channel Filter to Inbox Endpoint

**File to modify:** `backend/app/routers/videos.py`

**Changes:**
1. Add optional `channel_id` query parameter to `get_inbox_videos()`
2. Apply filter when parameter is provided

**Implementation:**

Find the existing endpoint:
```python
@router.get("/inbox", response_model=list[VideoResponse])
async def get_inbox_videos(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
```

Replace with:
```python
@router.get("/inbox", response_model=list[VideoResponse])
async def get_inbox_videos(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    channel_id: str | None = Query(None),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(Video)
        .options(selectinload(Video.channel))
        .where(Video.status == "inbox")
    )

    if channel_id:
        query = query.where(Video.channel_id == channel_id)

    query = query.order_by(Video.published_at.desc()).limit(limit).offset(offset)

    result = await db.execute(query)
    videos = result.scalars().all()
    return [video_to_response(v) for v in videos]
```

---

### Task 2: Frontend - Update API Client

**File to modify:** `frontend/src/api/client.ts`

**Changes:**
1. Update `getInbox` method to accept optional `channelId` parameter

**Implementation:**

Find the existing method:
```typescript
getInbox: () => api.get<Video[]>('/videos/inbox'),
```

Replace with:
```typescript
getInbox: (channelId?: string) =>
  api.get<Video[]>('/videos/inbox', {
    params: channelId ? { channel_id: channelId } : undefined
  }),
```

---

### Task 3: Frontend - Update useVideos Hook

**File to modify:** `frontend/src/hooks/useVideos.ts`

**Changes:**
1. Update `useInboxVideos()` to accept optional `channelId` parameter
2. Include `channelId` in query key for proper caching

**Implementation:**

Find the existing hook:
```typescript
export function useInboxVideos() {
  return useQuery({
    queryKey: ['videos', 'inbox'],
    queryFn: () => videosApi.getInbox().then(res => res.data),
  });
}
```

Replace with:
```typescript
export function useInboxVideos(channelId?: string) {
  return useQuery({
    queryKey: ['videos', 'inbox', channelId],
    queryFn: () => videosApi.getInbox(channelId).then(res => res.data),
  });
}
```

---

### Task 4: Frontend - Create ChannelVideoGroup Component

**File to create:** `frontend/src/components/video/ChannelVideoGroup.tsx`

**Purpose:** Collapsible section that displays videos for a single channel with per-channel bulk actions.

**Implementation:**

```typescript
import { useState } from 'react';
import { ChevronDownIcon, ChevronRightIcon } from '@heroicons/react/24/outline';
import { Video } from '../../types';
import VideoList from './VideoList';
import Button from '../common/Button';

interface ChannelVideoGroupProps {
  channelName: string;
  channelId: string;
  videos: Video[];
  onSave: (videoId: string) => void;
  onDiscard: (videoId: string) => void;
  onSaveAll: (videoIds: string[]) => void;
  onDiscardAll: (videoIds: string[]) => void;
  isSavingAll?: boolean;
  isDiscardingAll?: boolean;
  defaultExpanded?: boolean;
}

export default function ChannelVideoGroup({
  channelName,
  channelId,
  videos,
  onSave,
  onDiscard,
  onSaveAll,
  onDiscardAll,
  isSavingAll = false,
  isDiscardingAll = false,
  defaultExpanded = true,
}: ChannelVideoGroupProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const videoIds = videos.map(v => v.id);

  return (
    <div className="border border-gray-700 rounded-lg overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 bg-gray-800 hover:bg-gray-750 transition-colors"
      >
        <div className="flex items-center gap-3">
          {isExpanded ? (
            <ChevronDownIcon className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronRightIcon className="w-5 h-5 text-gray-400" />
          )}
          <span className="font-medium text-white">{channelName}</span>
          <span className="text-sm text-gray-400">({videos.length} video{videos.length !== 1 ? 's' : ''})</span>
        </div>

        {/* Per-channel bulk actions */}
        <div className="flex gap-2" onClick={e => e.stopPropagation()}>
          <Button
            variant="primary"
            size="sm"
            onClick={() => onSaveAll(videoIds)}
            disabled={isSavingAll || isDiscardingAll}
            loading={isSavingAll}
          >
            Save All
          </Button>
          <Button
            variant="secondary"
            size="sm"
            onClick={() => onDiscardAll(videoIds)}
            disabled={isSavingAll || isDiscardingAll}
            loading={isDiscardingAll}
          >
            Discard All
          </Button>
        </div>
      </button>

      {/* Video list */}
      {isExpanded && (
        <div className="p-4 bg-gray-900">
          <VideoList
            videos={videos}
            onSave={onSave}
            onDiscard={onDiscard}
            showSaveButton={true}
            showDiscardButton={true}
          />
        </div>
      )}
    </div>
  );
}
```

**Note:** If Button component doesn't have a `size` prop, you may need to add it or use className overrides.

---

### Task 5: Frontend - Create InboxViewToggle Component

**File to create:** `frontend/src/components/inbox/InboxViewToggle.tsx`

**Purpose:** Toggle between grouped and flat view modes.

**Implementation:**

```typescript
import { ListBulletIcon, RectangleStackIcon } from '@heroicons/react/24/outline';

export type InboxViewMode = 'flat' | 'grouped';

interface InboxViewToggleProps {
  viewMode: InboxViewMode;
  onChange: (mode: InboxViewMode) => void;
}

export default function InboxViewToggle({ viewMode, onChange }: InboxViewToggleProps) {
  return (
    <div className="flex rounded-lg overflow-hidden border border-gray-600">
      <button
        onClick={() => onChange('flat')}
        className={`flex items-center gap-1 px-3 py-1.5 text-sm transition-colors ${
          viewMode === 'flat'
            ? 'bg-gray-600 text-white'
            : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
        }`}
        title="Flat view"
      >
        <ListBulletIcon className="w-4 h-4" />
        <span>Flat</span>
      </button>
      <button
        onClick={() => onChange('grouped')}
        className={`flex items-center gap-1 px-3 py-1.5 text-sm transition-colors ${
          viewMode === 'grouped'
            ? 'bg-gray-600 text-white'
            : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
        }`}
        title="Grouped by channel"
      >
        <RectangleStackIcon className="w-4 h-4" />
        <span>Grouped</span>
      </button>
    </div>
  );
}
```

---

### Task 6: Frontend - Update Inbox Page

**File to modify:** `frontend/src/pages/Inbox.tsx`

**Changes:**
1. Add view mode state with localStorage persistence
2. Add view mode toggle to the header
3. Implement grouped view using ChannelVideoGroup
4. Keep flat view as the original VideoList
5. Add per-channel bulk action handling

**Implementation approach:**

1. Add imports at the top:
```typescript
import { useState, useEffect, useMemo } from 'react';
import ChannelVideoGroup from '../components/video/ChannelVideoGroup';
import InboxViewToggle, { InboxViewMode } from '../components/inbox/InboxViewToggle';
```

2. Add view mode state with localStorage:
```typescript
const [viewMode, setViewMode] = useState<InboxViewMode>(() => {
  const saved = localStorage.getItem('inbox-view-mode');
  return (saved as InboxViewMode) || 'grouped';
});

useEffect(() => {
  localStorage.setItem('inbox-view-mode', viewMode);
}, [viewMode]);
```

3. Group videos by channel using useMemo:
```typescript
const groupedVideos = useMemo(() => {
  if (!videos) return [];

  const groups = new Map<string, { channelName: string; channelId: string; videos: Video[] }>();

  for (const video of videos) {
    const channelId = video.channel_id;
    const existing = groups.get(channelId);

    if (existing) {
      existing.videos.push(video);
    } else {
      groups.set(channelId, {
        channelId,
        channelName: video.channel_name,
        videos: [video],
      });
    }
  }

  // Sort by video count (most videos first)
  return Array.from(groups.values()).sort((a, b) => b.videos.length - a.videos.length);
}, [videos]);
```

4. Add tracking for per-channel bulk actions:
```typescript
const [bulkActionChannelId, setBulkActionChannelId] = useState<string | null>(null);
const [bulkActionType, setBulkActionType] = useState<'save' | 'discard' | null>(null);

const handleChannelSaveAll = async (channelId: string, videoIds: string[]) => {
  setBulkActionChannelId(channelId);
  setBulkActionType('save');
  try {
    await bulkSave(videoIds);
  } finally {
    setBulkActionChannelId(null);
    setBulkActionType(null);
  }
};

const handleChannelDiscardAll = async (channelId: string, videoIds: string[]) => {
  setBulkActionChannelId(channelId);
  setBulkActionType('discard');
  try {
    await bulkDiscard(videoIds);
  } finally {
    setBulkActionChannelId(null);
    setBulkActionType(null);
  }
};
```

5. Update the JSX to include view toggle and conditional rendering:
```typescript
{/* Header with actions */}
<div className="flex items-center justify-between mb-6">
  <h1 className="text-2xl font-bold">
    Inbox {videos && videos.length > 0 && `(${videos.length} videos)`}
  </h1>
  <div className="flex items-center gap-4">
    <InboxViewToggle viewMode={viewMode} onChange={setViewMode} />
    {/* Existing buttons: Refresh, Save All, Discard All */}
  </div>
</div>

{/* Video content */}
{viewMode === 'flat' ? (
  <VideoList
    videos={videos || []}
    onSave={handleSave}
    onDiscard={handleDiscard}
    emptyMessage="No videos in inbox"
  />
) : (
  <div className="space-y-4">
    {groupedVideos.map(group => (
      <ChannelVideoGroup
        key={group.channelId}
        channelId={group.channelId}
        channelName={group.channelName}
        videos={group.videos}
        onSave={handleSave}
        onDiscard={handleDiscard}
        onSaveAll={(ids) => handleChannelSaveAll(group.channelId, ids)}
        onDiscardAll={(ids) => handleChannelDiscardAll(group.channelId, ids)}
        isSavingAll={bulkActionChannelId === group.channelId && bulkActionType === 'save'}
        isDiscardingAll={bulkActionChannelId === group.channelId && bulkActionType === 'discard'}
      />
    ))}
  </div>
)}
```

---

### Task 7: Add Size Variant to Button Component (if needed)

**File to modify:** `frontend/src/components/common/Button.tsx`

Check if the Button component already has a `size` prop. If not, add it:

```typescript
interface ButtonProps {
  // ... existing props
  size?: 'sm' | 'md' | 'lg';
}

// In the component, add size-based classes:
const sizeClasses = {
  sm: 'px-2 py-1 text-sm',
  md: 'px-4 py-2',
  lg: 'px-6 py-3 text-lg',
};

// Apply in className:
className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size || 'md']} ${className}`}
```

---

## File Summary

### Files to Create
1. `frontend/src/components/video/ChannelVideoGroup.tsx`
2. `frontend/src/components/inbox/InboxViewToggle.tsx`

### Files to Modify
1. `backend/app/routers/videos.py` - Add `channel_id` filter parameter
2. `frontend/src/api/client.ts` - Update `getInbox` method
3. `frontend/src/hooks/useVideos.ts` - Update `useInboxVideos` hook
4. `frontend/src/pages/Inbox.tsx` - Add grouped view mode
5. `frontend/src/components/common/Button.tsx` - Add size prop (if needed)

---

## Testing Checklist

- [ ] Backend: Verify `/api/videos/inbox` works without `channel_id` parameter
- [ ] Backend: Verify `/api/videos/inbox?channel_id=xxx` filters correctly
- [ ] Frontend: View mode toggle switches between flat and grouped
- [ ] Frontend: View mode preference persists across page refreshes
- [ ] Frontend: Grouped view shows all channels with correct video counts
- [ ] Frontend: Collapsing/expanding channel sections works
- [ ] Frontend: Per-channel Save All works correctly
- [ ] Frontend: Per-channel Discard All works correctly
- [ ] Frontend: Global Save All still works in flat view
- [ ] Frontend: Global Discard All still works in flat view
- [ ] Frontend: Empty state displays correctly when inbox is empty
- [ ] Frontend: Loading state displays correctly
- [ ] Frontend: Error state with retry button works

---

## Dependencies

- `@heroicons/react` - Already installed (check existing icon usage)
- No new npm packages required

---

## Notes

- The grouped view defaults to expanded for better initial visibility
- Channels are sorted by video count (most videos first) to prioritize channels with more content
- Per-channel bulk actions allow triaging one channel at a time without affecting others
- The flat view remains available for users who prefer the original layout
