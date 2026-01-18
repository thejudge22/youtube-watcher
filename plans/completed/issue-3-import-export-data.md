# Issue #3: Import/Export Data - Development Plan

## ✅ Status: COMPLETED in v1.3.0

## Overview

Add functionality to export and import channels and saved videos in JSON format, plus import videos from a text file containing YouTube URLs.

**Priority:** Medium-High (Foundation Feature)
**Backend Changes:** New router with 6 endpoints
**Frontend Changes:** New Settings section with import/export UI
**Completed:** 2026-01-17

---

## Current State

### Database Models

**Channel Model** (`backend/app/models/channel.py`):
```python
- id: String (UUID)
- youtube_channel_id: String (unique)
- name: String
- rss_url: String
- youtube_url: String
- thumbnail_url: String
- last_checked: DateTime
- last_video_id: String
- created_at: DateTime
- updated_at: DateTime
```

**Video Model** (`backend/app/models/video.py`):
```python
- id: String (UUID)
- youtube_video_id: String (unique)
- channel_id: ForeignKey
- title: String
- description: String
- thumbnail_url: String
- video_url: String
- published_at: DateTime
- status: String ('inbox', 'saved', 'discarded')
- saved_at: DateTime
- discarded_at: DateTime
- created_at: DateTime
```

### Existing Related Functionality

**Add Video from URL** (`backend/app/routers/videos.py`):
- `POST /api/videos/from-url` - Adds a single video by YouTube URL
- Uses `fetch_video_by_id()` from `backend/app/services/youtube.py`
- Returns the created video or existing video if already in database

### Settings Page
**File:** `frontend/src/pages/Settings.tsx`
- Currently has "Data Management" section with danger zone actions
- Good location to add Import/Export section

---

## JSON Schema Design

### Export Format

```json
{
  "version": "1.0",
  "exported_at": "2026-01-15T10:00:00Z",
  "channels": [
    {
      "youtube_channel_id": "UCxxxxxxxxxxxxxxxx",
      "name": "Channel Name",
      "youtube_url": "https://www.youtube.com/channel/UCxxxxxxxxxxxxxxxx"
    }
  ],
  "saved_videos": [
    {
      "youtube_video_id": "abc123def45",
      "title": "Video Title",
      "video_url": "https://www.youtube.com/watch?v=abc123def45",
      "channel_youtube_id": "UCxxxxxxxxxxxxxxxx",
      "channel_name": "Channel Name",
      "saved_at": "2026-01-10T12:00:00Z",
      "published_at": "2026-01-05T08:00:00Z"
    }
  ]
}
```

### Import Format

Same as export format. Fields `version` and `exported_at` are optional during import.

---

## Implementation Tasks

### Task 1: Create Pydantic Schemas for Import/Export

**File to create:** `backend/app/schemas/import_export.py`

**Implementation:**

```python
from datetime import datetime
from pydantic import BaseModel


class ChannelExport(BaseModel):
    youtube_channel_id: str
    name: str
    youtube_url: str


class VideoExport(BaseModel):
    youtube_video_id: str
    title: str
    video_url: str
    channel_youtube_id: str | None = None
    channel_name: str | None = None
    saved_at: datetime | None = None
    published_at: datetime | None = None


class ExportData(BaseModel):
    version: str = "1.0"
    exported_at: datetime
    channels: list[ChannelExport]
    saved_videos: list[VideoExport]


class ImportChannelsRequest(BaseModel):
    channels: list[ChannelExport]


class ImportVideosRequest(BaseModel):
    videos: list[VideoExport]


class ImportUrlsRequest(BaseModel):
    urls: list[str]


class ImportResult(BaseModel):
    total: int
    imported: int
    skipped: int
    errors: list[str]


class ChannelImportResult(ImportResult):
    pass


class VideoImportResult(ImportResult):
    pass
```

---

### Task 2: Create Import/Export Router

**File to create:** `backend/app/routers/import_export.py`

**Endpoints to implement:**
1. `GET /api/export/channels` - Export all channels
2. `GET /api/export/saved-videos` - Export all saved videos
3. `GET /api/export/all` - Export channels and saved videos combined
4. `POST /api/import/channels` - Import channels from JSON
5. `POST /api/import/videos` - Import saved videos from JSON
6. `POST /api/import/video-urls` - Import videos from URL list

**Implementation:**

```python
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database import get_db
from ..models.channel import Channel
from ..models.video import Video
from ..schemas.import_export import (
    ChannelExport,
    VideoExport,
    ExportData,
    ImportChannelsRequest,
    ImportVideosRequest,
    ImportUrlsRequest,
    ChannelImportResult,
    VideoImportResult,
)
from ..services.youtube import (
    extract_channel_id,
    fetch_channel_info,
    fetch_video_by_id,
    extract_video_id,
)

router = APIRouter(prefix="/import-export", tags=["import-export"])


# ============ EXPORT ENDPOINTS ============

@router.get("/export/channels")
async def export_channels(db: AsyncSession = Depends(get_db)):
    """Export all channels as JSON."""
    result = await db.execute(select(Channel).order_by(Channel.name))
    channels = result.scalars().all()

    channel_exports = [
        ChannelExport(
            youtube_channel_id=c.youtube_channel_id,
            name=c.name,
            youtube_url=c.youtube_url,
        )
        for c in channels
    ]

    export_data = ExportData(
        version="1.0",
        exported_at=datetime.now(timezone.utc),
        channels=channel_exports,
        saved_videos=[],
    )

    return JSONResponse(
        content=export_data.model_dump(mode="json"),
        headers={
            "Content-Disposition": f'attachment; filename="youtube-watcher-channels-{datetime.now().strftime("%Y%m%d")}.json"'
        },
    )


@router.get("/export/saved-videos")
async def export_saved_videos(db: AsyncSession = Depends(get_db)):
    """Export all saved videos as JSON."""
    result = await db.execute(
        select(Video)
        .options(selectinload(Video.channel))
        .where(Video.status == "saved")
        .order_by(Video.saved_at.desc())
    )
    videos = result.scalars().all()

    video_exports = [
        VideoExport(
            youtube_video_id=v.youtube_video_id,
            title=v.title,
            video_url=v.video_url,
            channel_youtube_id=v.channel.youtube_channel_id if v.channel else None,
            channel_name=v.channel.name if v.channel else None,
            saved_at=v.saved_at,
            published_at=v.published_at,
        )
        for v in videos
    ]

    export_data = ExportData(
        version="1.0",
        exported_at=datetime.now(timezone.utc),
        channels=[],
        saved_videos=video_exports,
    )

    return JSONResponse(
        content=export_data.model_dump(mode="json"),
        headers={
            "Content-Disposition": f'attachment; filename="youtube-watcher-saved-videos-{datetime.now().strftime("%Y%m%d")}.json"'
        },
    )


@router.get("/export/all")
async def export_all(db: AsyncSession = Depends(get_db)):
    """Export all channels and saved videos as JSON."""
    # Fetch channels
    channels_result = await db.execute(select(Channel).order_by(Channel.name))
    channels = channels_result.scalars().all()

    channel_exports = [
        ChannelExport(
            youtube_channel_id=c.youtube_channel_id,
            name=c.name,
            youtube_url=c.youtube_url,
        )
        for c in channels
    ]

    # Fetch saved videos
    videos_result = await db.execute(
        select(Video)
        .options(selectinload(Video.channel))
        .where(Video.status == "saved")
        .order_by(Video.saved_at.desc())
    )
    videos = videos_result.scalars().all()

    video_exports = [
        VideoExport(
            youtube_video_id=v.youtube_video_id,
            title=v.title,
            video_url=v.video_url,
            channel_youtube_id=v.channel.youtube_channel_id if v.channel else None,
            channel_name=v.channel.name if v.channel else None,
            saved_at=v.saved_at,
            published_at=v.published_at,
        )
        for v in videos
    ]

    export_data = ExportData(
        version="1.0",
        exported_at=datetime.now(timezone.utc),
        channels=channel_exports,
        saved_videos=video_exports,
    )

    return JSONResponse(
        content=export_data.model_dump(mode="json"),
        headers={
            "Content-Disposition": f'attachment; filename="youtube-watcher-export-{datetime.now().strftime("%Y%m%d")}.json"'
        },
    )


# ============ IMPORT ENDPOINTS ============

@router.post("/import/channels", response_model=ChannelImportResult)
async def import_channels(
    request: ImportChannelsRequest,
    db: AsyncSession = Depends(get_db),
):
    """Import channels from JSON. Skips existing channels."""
    total = len(request.channels)
    imported = 0
    skipped = 0
    errors: list[str] = []

    for channel_data in request.channels:
        try:
            # Check if channel already exists
            existing = await db.execute(
                select(Channel).where(
                    Channel.youtube_channel_id == channel_data.youtube_channel_id
                )
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue

            # Fetch full channel info from YouTube
            channel_info = await fetch_channel_info(channel_data.youtube_url)
            if not channel_info:
                errors.append(f"Could not fetch info for channel: {channel_data.name}")
                continue

            # Create new channel
            new_channel = Channel(
                youtube_channel_id=channel_info["youtube_channel_id"],
                name=channel_info["name"],
                rss_url=channel_info["rss_url"],
                youtube_url=channel_info["youtube_url"],
                thumbnail_url=channel_info.get("thumbnail_url"),
                last_checked=datetime.now(timezone.utc),
            )
            db.add(new_channel)
            await db.flush()
            imported += 1

        except Exception as e:
            errors.append(f"Error importing {channel_data.name}: {str(e)}")

    await db.commit()

    return ChannelImportResult(
        total=total,
        imported=imported,
        skipped=skipped,
        errors=errors,
    )


@router.post("/import/videos", response_model=VideoImportResult)
async def import_videos(
    request: ImportVideosRequest,
    db: AsyncSession = Depends(get_db),
):
    """Import saved videos from JSON. Skips existing videos."""
    total = len(request.videos)
    imported = 0
    skipped = 0
    errors: list[str] = []

    for video_data in request.videos:
        try:
            # Check if video already exists
            existing = await db.execute(
                select(Video).where(
                    Video.youtube_video_id == video_data.youtube_video_id
                )
            )
            existing_video = existing.scalar_one_or_none()

            if existing_video:
                # If video exists but not saved, mark it as saved
                if existing_video.status != "saved":
                    existing_video.status = "saved"
                    existing_video.saved_at = video_data.saved_at or datetime.now(timezone.utc)
                    imported += 1
                else:
                    skipped += 1
                continue

            # Fetch video info from YouTube
            video_info = await fetch_video_by_id(video_data.youtube_video_id)
            if not video_info:
                errors.append(f"Could not fetch video: {video_data.youtube_video_id}")
                continue

            # Find or skip channel association
            channel_id = None
            if video_info.get("channel_id"):
                channel_result = await db.execute(
                    select(Channel).where(
                        Channel.youtube_channel_id == video_info["channel_id"]
                    )
                )
                channel = channel_result.scalar_one_or_none()
                if channel:
                    channel_id = channel.id

            # Create new video as saved
            new_video = Video(
                youtube_video_id=video_info["youtube_video_id"],
                channel_id=channel_id,
                title=video_info["title"],
                description=video_info.get("description", ""),
                thumbnail_url=video_info["thumbnail_url"],
                video_url=video_info["video_url"],
                published_at=video_info["published_at"],
                status="saved",
                saved_at=video_data.saved_at or datetime.now(timezone.utc),
            )
            db.add(new_video)
            await db.flush()
            imported += 1

        except Exception as e:
            errors.append(f"Error importing video {video_data.youtube_video_id}: {str(e)}")

    await db.commit()

    return VideoImportResult(
        total=total,
        imported=imported,
        skipped=skipped,
        errors=errors,
    )


@router.post("/import/video-urls", response_model=VideoImportResult)
async def import_video_urls(
    request: ImportUrlsRequest,
    db: AsyncSession = Depends(get_db),
):
    """Import videos from a list of YouTube URLs. Videos are added as saved."""
    total = len(request.urls)
    imported = 0
    skipped = 0
    errors: list[str] = []

    for url in request.urls:
        url = url.strip()
        if not url:
            continue

        try:
            # Extract video ID from URL
            video_id = extract_video_id(url)
            if not video_id:
                errors.append(f"Invalid YouTube URL: {url}")
                continue

            # Check if video already exists
            existing = await db.execute(
                select(Video).where(Video.youtube_video_id == video_id)
            )
            existing_video = existing.scalar_one_or_none()

            if existing_video:
                if existing_video.status != "saved":
                    existing_video.status = "saved"
                    existing_video.saved_at = datetime.now(timezone.utc)
                    imported += 1
                else:
                    skipped += 1
                continue

            # Fetch video info from YouTube
            video_info = await fetch_video_by_id(video_id)
            if not video_info:
                errors.append(f"Could not fetch video: {url}")
                continue

            # Find channel association
            channel_id = None
            if video_info.get("channel_id"):
                channel_result = await db.execute(
                    select(Channel).where(
                        Channel.youtube_channel_id == video_info["channel_id"]
                    )
                )
                channel = channel_result.scalar_one_or_none()
                if channel:
                    channel_id = channel.id

            # Create new video as saved
            new_video = Video(
                youtube_video_id=video_info["youtube_video_id"],
                channel_id=channel_id,
                title=video_info["title"],
                description=video_info.get("description", ""),
                thumbnail_url=video_info["thumbnail_url"],
                video_url=video_info["video_url"],
                published_at=video_info["published_at"],
                status="saved",
                saved_at=datetime.now(timezone.utc),
            )
            db.add(new_video)
            await db.flush()
            imported += 1

        except Exception as e:
            errors.append(f"Error importing {url}: {str(e)}")

    await db.commit()

    return VideoImportResult(
        total=total,
        imported=imported,
        skipped=skipped,
        errors=errors,
    )
```

---

### Task 3: Register Router in Main App

**File to modify:** `backend/app/main.py`

**Changes:**
1. Import the new router
2. Register it with the app

Find the router imports section and add:
```python
from .routers import import_export
```

Find where routers are registered (look for `app.include_router`) and add:
```python
app.include_router(import_export.router, prefix="/api")
```

---

### Task 4: Update Frontend API Client

**File to modify:** `frontend/src/api/client.ts`

**Changes:**
1. Add import/export API methods
2. Add TypeScript types for responses

Add to the existing types section or create new types:
```typescript
export interface ImportResult {
  total: number;
  imported: number;
  skipped: number;
  errors: string[];
}

export interface ExportData {
  version: string;
  exported_at: string;
  channels: Array<{
    youtube_channel_id: string;
    name: string;
    youtube_url: string;
  }>;
  saved_videos: Array<{
    youtube_video_id: string;
    title: string;
    video_url: string;
    channel_youtube_id: string | null;
    channel_name: string | null;
    saved_at: string | null;
    published_at: string | null;
  }>;
}
```

Add new API namespace:
```typescript
export const importExportApi = {
  // Export endpoints - these return file downloads
  exportChannels: () => api.get<ExportData>('/import-export/export/channels'),
  exportSavedVideos: () => api.get<ExportData>('/import-export/export/saved-videos'),
  exportAll: () => api.get<ExportData>('/import-export/export/all'),

  // Import endpoints
  importChannels: (channels: ExportData['channels']) =>
    api.post<ImportResult>('/import-export/import/channels', { channels }),

  importVideos: (videos: ExportData['saved_videos']) =>
    api.post<ImportResult>('/import-export/import/videos', { videos }),

  importVideoUrls: (urls: string[]) =>
    api.post<ImportResult>('/import-export/import/video-urls', { urls }),
};
```

---

### Task 5: Create Import/Export Hooks

**File to create:** `frontend/src/hooks/useImportExport.ts`

**Implementation:**

```typescript
import { useMutation, useQueryClient } from '@tanstack/react-query';
import { importExportApi, ExportData, ImportResult } from '../api/client';

export function useExportChannels() {
  return useMutation({
    mutationFn: async () => {
      const response = await importExportApi.exportChannels();
      downloadJson(response.data, 'youtube-watcher-channels');
    },
  });
}

export function useExportSavedVideos() {
  return useMutation({
    mutationFn: async () => {
      const response = await importExportApi.exportSavedVideos();
      downloadJson(response.data, 'youtube-watcher-saved-videos');
    },
  });
}

export function useExportAll() {
  return useMutation({
    mutationFn: async () => {
      const response = await importExportApi.exportAll();
      downloadJson(response.data, 'youtube-watcher-export');
    },
  });
}

export function useImportChannels() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (channels: ExportData['channels']) =>
      importExportApi.importChannels(channels).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['channels'] });
    },
  });
}

export function useImportVideos() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (videos: ExportData['saved_videos']) =>
      importExportApi.importVideos(videos).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
    },
  });
}

export function useImportVideoUrls() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (urls: string[]) =>
      importExportApi.importVideoUrls(urls).then(res => res.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['videos'] });
    },
  });
}

// Helper function to trigger file download
function downloadJson(data: ExportData, filename: string) {
  const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `${filename}-${new Date().toISOString().split('T')[0]}.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
```

---

### Task 6: Create ImportExportSection Component

**File to create:** `frontend/src/components/settings/ImportExportSection.tsx`

**Implementation:**

```typescript
import { useState, useRef } from 'react';
import {
  useExportChannels,
  useExportSavedVideos,
  useExportAll,
  useImportChannels,
  useImportVideos,
  useImportVideoUrls,
} from '../../hooks/useImportExport';
import { ExportData, ImportResult } from '../../api/client';
import Button from '../common/Button';

export default function ImportExportSection() {
  const [importResult, setImportResult] = useState<ImportResult | null>(null);
  const [importError, setImportError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const urlFileInputRef = useRef<HTMLInputElement>(null);

  const exportChannels = useExportChannels();
  const exportSavedVideos = useExportSavedVideos();
  const exportAll = useExportAll();
  const importChannels = useImportChannels();
  const importVideos = useImportVideos();
  const importVideoUrls = useImportVideoUrls();

  const handleFileUpload = async (
    event: React.ChangeEvent<HTMLInputElement>,
    type: 'channels' | 'videos' | 'all'
  ) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setImportResult(null);
    setImportError(null);

    try {
      const text = await file.text();
      const data: ExportData = JSON.parse(text);

      let result: ImportResult;

      if (type === 'channels' || type === 'all') {
        if (data.channels && data.channels.length > 0) {
          result = await importChannels.mutateAsync(data.channels);
          setImportResult(result);
        }
      }

      if (type === 'videos' || type === 'all') {
        if (data.saved_videos && data.saved_videos.length > 0) {
          result = await importVideos.mutateAsync(data.saved_videos);
          setImportResult(prev => prev ? {
            total: prev.total + result.total,
            imported: prev.imported + result.imported,
            skipped: prev.skipped + result.skipped,
            errors: [...prev.errors, ...result.errors],
          } : result);
        }
      }
    } catch (err) {
      setImportError(err instanceof Error ? err.message : 'Failed to parse file');
    }

    // Reset input
    event.target.value = '';
  };

  const handleUrlFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setImportResult(null);
    setImportError(null);

    try {
      const text = await file.text();
      const urls = text
        .split('\n')
        .map(line => line.trim())
        .filter(line => line && !line.startsWith('#'));

      if (urls.length === 0) {
        setImportError('No valid URLs found in file');
        return;
      }

      const result = await importVideoUrls.mutateAsync(urls);
      setImportResult(result);
    } catch (err) {
      setImportError(err instanceof Error ? err.message : 'Failed to process file');
    }

    // Reset input
    event.target.value = '';
  };

  const isExporting = exportChannels.isPending || exportSavedVideos.isPending || exportAll.isPending;
  const isImporting = importChannels.isPending || importVideos.isPending || importVideoUrls.isPending;

  return (
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Import / Export</h2>

      {/* Export Section */}
      <div className="bg-gray-800 rounded-lg p-4 space-y-4">
        <h3 className="font-medium">Export Data</h3>
        <p className="text-sm text-gray-400">
          Download your data as JSON files for backup or migration.
        </p>
        <div className="flex flex-wrap gap-2">
          <Button
            variant="secondary"
            onClick={() => exportChannels.mutate()}
            loading={exportChannels.isPending}
            disabled={isExporting}
          >
            Export Channels
          </Button>
          <Button
            variant="secondary"
            onClick={() => exportSavedVideos.mutate()}
            loading={exportSavedVideos.isPending}
            disabled={isExporting}
          >
            Export Saved Videos
          </Button>
          <Button
            variant="primary"
            onClick={() => exportAll.mutate()}
            loading={exportAll.isPending}
            disabled={isExporting}
          >
            Export All
          </Button>
        </div>
      </div>

      {/* Import Section */}
      <div className="bg-gray-800 rounded-lg p-4 space-y-4">
        <h3 className="font-medium">Import Data</h3>
        <p className="text-sm text-gray-400">
          Import channels and videos from JSON files or YouTube URLs.
        </p>

        <div className="space-y-3">
          {/* JSON Import */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              Import from JSON (channels, videos, or combined export)
            </label>
            <input
              ref={fileInputRef}
              type="file"
              accept=".json"
              onChange={(e) => handleFileUpload(e, 'all')}
              className="hidden"
            />
            <Button
              variant="secondary"
              onClick={() => fileInputRef.current?.click()}
              loading={importChannels.isPending || importVideos.isPending}
              disabled={isImporting}
            >
              Choose JSON File
            </Button>
          </div>

          {/* URL Import */}
          <div>
            <label className="block text-sm text-gray-400 mb-2">
              Import from URL list (text file with one URL per line)
            </label>
            <input
              ref={urlFileInputRef}
              type="file"
              accept=".txt"
              onChange={handleUrlFileUpload}
              className="hidden"
            />
            <Button
              variant="secondary"
              onClick={() => urlFileInputRef.current?.click()}
              loading={importVideoUrls.isPending}
              disabled={isImporting}
            >
              Choose URL File
            </Button>
          </div>
        </div>

        {/* Import Result */}
        {importResult && (
          <div className="mt-4 p-3 bg-gray-700 rounded">
            <p className="font-medium text-green-400">Import Complete</p>
            <p className="text-sm text-gray-300 mt-1">
              Imported: {importResult.imported} | Skipped: {importResult.skipped} | Total: {importResult.total}
            </p>
            {importResult.errors.length > 0 && (
              <div className="mt-2">
                <p className="text-sm text-red-400">Errors ({importResult.errors.length}):</p>
                <ul className="text-xs text-gray-400 mt-1 max-h-32 overflow-y-auto">
                  {importResult.errors.map((error, i) => (
                    <li key={i}>• {error}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {/* Import Error */}
        {importError && (
          <div className="mt-4 p-3 bg-red-900/50 rounded">
            <p className="text-red-400">{importError}</p>
          </div>
        )}
      </div>
    </div>
  );
}
```

---

### Task 7: Update Settings Page

**File to modify:** `frontend/src/pages/Settings.tsx`

**Changes:**
1. Import ImportExportSection component
2. Add it before the Data Management section

Add import:
```typescript
import ImportExportSection from '../components/settings/ImportExportSection';
```

Add the section in the JSX (before Data Management):
```typescript
return (
  <div className="max-w-2xl mx-auto space-y-8">
    <h1 className="text-2xl font-bold">Settings</h1>

    {/* Import/Export Section */}
    <ImportExportSection />

    {/* Existing Data Management Section */}
    <div className="space-y-6">
      <h2 className="text-xl font-semibold">Data Management</h2>
      {/* ... existing content ... */}
    </div>
  </div>
);
```

---

### Task 8: Verify YouTube Service Functions

**File to check:** `backend/app/services/youtube.py`

Ensure these functions exist and work correctly:
- `fetch_channel_info(url)` - Fetches channel info from YouTube URL
- `fetch_video_by_id(video_id)` - Fetches video info by YouTube video ID
- `extract_video_id(url)` - Extracts video ID from YouTube URL

If `extract_video_id` doesn't exist, add it:
```python
import re

def extract_video_id(url: str) -> str | None:
    """Extract YouTube video ID from various URL formats."""
    patterns = [
        r'(?:youtube\.com/watch\?v=|youtu\.be/|youtube\.com/embed/)([a-zA-Z0-9_-]{11})',
        r'youtube\.com/shorts/([a-zA-Z0-9_-]{11})',
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None
```

---

## File Summary

### Files to Create
1. `backend/app/schemas/import_export.py` - Pydantic schemas
2. `backend/app/routers/import_export.py` - API endpoints
3. `frontend/src/hooks/useImportExport.ts` - React Query hooks
4. `frontend/src/components/settings/ImportExportSection.tsx` - UI component

### Files to Modify
1. `backend/app/main.py` - Register new router
2. `frontend/src/api/client.ts` - Add API methods
3. `frontend/src/pages/Settings.tsx` - Add ImportExportSection
4. `backend/app/services/youtube.py` - Add `extract_video_id` if missing

---

## Testing Checklist

### Export Tests
- [ ] Export Channels downloads JSON file with correct structure
- [ ] Export Saved Videos downloads JSON file with correct structure
- [ ] Export All downloads combined JSON file
- [ ] Export files have correct filename with date
- [ ] Empty exports work correctly (empty arrays)

### Import Tests
- [ ] Import channels from JSON works (new channels)
- [ ] Import channels skips existing channels
- [ ] Import videos from JSON works (new videos)
- [ ] Import videos marks existing non-saved videos as saved
- [ ] Import videos skips already saved videos
- [ ] Import video URLs from text file works
- [ ] Invalid URLs in file are reported as errors
- [ ] Import shows correct counts (imported/skipped/errors)
- [ ] Import errors are displayed to user
- [ ] Large imports complete without timeout (test with 50+ items)

### Edge Cases
- [ ] Invalid JSON file shows error
- [ ] Empty file shows appropriate message
- [ ] File with only comments (# lines) handled correctly
- [ ] Mixed valid/invalid URLs handled correctly
- [ ] Network errors during fetch are reported

---

## Dependencies

- No new npm packages required
- No new Python packages required
- Uses existing YouTube service functions

---

## Notes

- Import operations are idempotent - running the same import twice will skip already imported items
- Videos imported without a matching channel will have `channel_id` as null
- The URL import feature is useful for migrating from browser bookmarks or other services
- Consider adding a progress indicator for large imports (future enhancement)
- Rate limiting should be considered for YouTube API calls during bulk imports
