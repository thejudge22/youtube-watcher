# YouTube-Watcher Implementation Plan

> **For AI Pair Programmers**: This document contains detailed implementation instructions.
> Follow each phase sequentially, testing and committing after each milestone.

---

## Table of Contents

1. [Project Context](#project-context)
2. [Technical Requirements](#technical-requirements)
3. [Implementation Phases](#implementation-phases)
4. [Phase Details](#phase-details)
5. [Testing Guidelines](#testing-guidelines)
6. [Git Workflow](#git-workflow)
7. [Common Pitfalls](#common-pitfalls)

---

## Project Status

| Phase | Name | Status | Git Tag |
|-------|------|--------|---------|
| 1A | Project Scaffold | ✅ Complete | `v0.1.0-scaffold` |
| 1B | Docker Setup | ✅ Complete | `v0.1.1-docker` |
| 2A | Database & Models | ✅ Complete | `v0.2.0-models` |
| 2B | RSS Service | ✅ Complete | `v0.2.1-rss` |
| 2C | Channel API | ✅ Complete | `v0.2.2-channels-api` |
| 2D | Video API | ✅ Complete | `v0.2.3-videos-api` |
| 3A | Frontend Scaffold | ⏳ Pending | `v0.3.0-frontend-scaffold` |
| 3B | API Client | ⏳ Pending | `v0.3.1-api-client` |
| 3C | Channel Management UI | ⏳ Pending | `v0.3.2-channels-ui` |
| 4A | Inbox Page | ⏳ Pending | `v0.4.0-inbox` |
| 4B | Saved Videos Page | ⏳ Pending | `v0.4.1-saved` |
| 5 | Direct URL Save | ⏳ Pending | `v0.5.0-url-save` |
| 6 | Polish | ⏳ Pending | `v1.0.0` |

**Current Phase**: Phase 2D - Video API (Complete)

**Next Phase**: Phase 3A - Frontend Scaffold

---

## Project Context

### What We're Building

A self-hosted web application that:
1. Tracks YouTube channels via RSS feeds
2. Shows new videos in an "inbox" for the user to triage
3. Saves videos to a "watch later" list
4. Allows filtering and sorting of saved videos

### Key Decisions Made

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Data Source | YouTube RSS Feeds | No API key needed, simpler setup |
| Database | SQLite | Single-user app, no separate DB server |
| Backend | Python + FastAPI | Async support, auto API docs, type safety |
| Frontend | React + TypeScript | Component-based, good ecosystem |
| Styling | TailwindCSS | Rapid UI development |
| Auth | None | Single-user personal tool |
| Video Checks | User-initiated | No background tasks/cron |
| Deployment | Single Docker container | FastAPI serves both API and static frontend |

### YouTube RSS Feed Format

```
URL: https://www.youtube.com/feeds/videos.xml?channel_id=CHANNEL_ID
```

Example feed entry structure:
```xml
<entry>
  <yt:videoId>VIDEO_ID</yt:videoId>
  <title>Video Title</title>
  <author><name>Channel Name</name></author>
  <published>2024-01-15T10:00:00+00:00</published>
  <media:group>
    <media:thumbnail url="https://i.ytimg.com/vi/VIDEO_ID/hqdefault.jpg"/>
    <media:description>Video description...</media:description>
  </media:group>
</entry>
```

---

## Technical Requirements

### Directory Structure

```
youtube-watcher/
├── Dockerfile              # Single container: builds frontend + runs backend
├── docker-compose.yml      # Simple single-service configuration
├── .env.example
├── .env                    # Created from .env.example, gitignored
├── README.md
├── agents.md
├── data/                   # SQLite database location, gitignored
│   └── .gitkeep
│
├── backend/
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   └── app/
│       ├── __init__.py
│       ├── main.py         # Serves API at /api/* AND static files at /*
│       ├── config.py
│       ├── database.py
│       ├── models/
│       │   ├── __init__.py
│       │   ├── channel.py
│       │   └── video.py
│       ├── schemas/
│       │   ├── __init__.py
│       │   ├── channel.py
│       │   └── video.py
│       ├── routers/
│       │   ├── __init__.py
│       │   ├── channels.py
│       │   └── videos.py
│       └── services/
│           ├── __init__.py
│           ├── rss_parser.py
│           └── youtube_utils.py
│
├── frontend/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── postcss.config.js
│   ├── vite.config.ts
│   ├── index.html
│   └── src/
│       ├── main.tsx
│       ├── App.tsx
│       ├── index.css
│       ├── api/
│       │   └── client.ts
│       ├── components/
│       │   ├── layout/
│       │   │   ├── Header.tsx
│       │   │   └── Navigation.tsx
│       │   ├── channel/
│       │   │   ├── ChannelCard.tsx
│       │   │   ├── ChannelList.tsx
│       │   │   └── AddChannelModal.tsx
│       │   ├── video/
│       │   │   ├── VideoCard.tsx
│       │   │   └── VideoList.tsx
│       │   └── common/
│       │       ├── Button.tsx
│       │       ├── Modal.tsx
│       │       └── LoadingSpinner.tsx
│       ├── pages/
│       │   ├── Inbox.tsx
│       │   ├── Saved.tsx
│       │   └── Channels.tsx
│       ├── hooks/
│       │   ├── useChannels.ts
│       │   └── useVideos.ts
│       └── types/
│           └── index.ts
│
└── plans/
    ├── development-plan.md
    └── plan.md
```

### Single Container Architecture

The application uses a single Docker container that:
1. **Build stage**: Compiles the React frontend to static files
2. **Runtime**: FastAPI serves both the API (`/api/*`) and static frontend files (`/*`)

This simplifies deployment significantly - one image, one container, one port.

### Database Schema

```sql
-- channels table
CREATE TABLE channels (
    id TEXT PRIMARY KEY,  -- UUID
    youtube_channel_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    rss_url TEXT NOT NULL,
    thumbnail_url TEXT,
    last_checked TIMESTAMP,
    last_video_id TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- videos table
CREATE TABLE videos (
    id TEXT PRIMARY KEY,  -- UUID
    youtube_video_id TEXT UNIQUE NOT NULL,
    channel_id TEXT REFERENCES channels(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    thumbnail_url TEXT,
    video_url TEXT NOT NULL,
    published_at TIMESTAMP NOT NULL,
    status TEXT NOT NULL DEFAULT 'inbox',  -- 'inbox', 'saved', 'discarded'
    saved_at TIMESTAMP,
    discarded_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX idx_videos_status ON videos(status);
CREATE INDEX idx_videos_channel_id ON videos(channel_id);
CREATE INDEX idx_videos_published_at ON videos(published_at);
CREATE INDEX idx_videos_saved_at ON videos(saved_at);
```

### API Endpoints

| Method | Endpoint | Request Body | Response |
|--------|----------|--------------|----------|
| GET | `/api/channels` | - | List of channels |
| POST | `/api/channels` | `{url: string}` | Created channel + initial videos |
| DELETE | `/api/channels/{id}` | - | 204 No Content |
| POST | `/api/channels/{id}/refresh` | - | New videos found |
| POST | `/api/channels/refresh-all` | - | Summary of new videos |
| GET | `/api/videos/inbox` | - | Inbox videos |
| GET | `/api/videos/saved?channel_id=&sort_by=&order=` | - | Saved videos |
| POST | `/api/videos/{id}/save` | - | Updated video |
| POST | `/api/videos/{id}/discard` | - | Updated video |
| POST | `/api/videos/bulk-save` | `{video_ids: string[]}` | Updated videos |
| POST | `/api/videos/bulk-discard` | `{video_ids: string[]}` | Updated videos |
| POST | `/api/videos/from-url` | `{url: string}` | Created video |
| DELETE | `/api/videos/{id}` | - | 204 No Content |
| GET | `/api/health` | - | `{status: "ok"}` |

---

## Implementation Phases

### Overview

| Phase | Name | Deliverables | Git Tag |
|-------|------|--------------|---------|
| 1A | Project Scaffold | Basic file structure, configs | `v0.1.0-scaffold` |
| 1B | Docker Setup | Working containers | `v0.1.1-docker` |
| 2A | Database & Models | SQLAlchemy models, migrations | `v0.2.0-models` |
| 2B | RSS Service | Feed parsing, URL resolution | `v0.2.1-rss` |
| 2C | Channel API | CRUD endpoints for channels | `v0.2.2-channels-api` |
| 2D | Video API | Video management endpoints | `v0.2.3-videos-api` |
| 3A | Frontend Scaffold | React app, routing, layout | `v0.3.0-frontend-scaffold` |
| 3B | API Client | TypeScript API client | `v0.3.1-api-client` |
| 3C | Channel Management UI | Channels page complete | `v0.3.2-channels-ui` |
| 4A | Inbox Page | Video inbox with actions | `v0.4.0-inbox` |
| 4B | Saved Videos Page | Filtering, sorting | `v0.4.1-saved` |
| 5 | Direct URL Save | Paste URL feature | `v0.5.0-url-save` |
| 6 | Polish | Error handling, loading states | `v1.0.0` |

---

## Phase Details

### Phase 1A: Project Scaffold

**Goal**: Create basic project structure and configuration files.

**Tasks**:
1. Create directory structure as specified above
2. Create `backend/requirements.txt`:
   ```
   fastapi==0.109.0
   uvicorn[standard]==0.27.0
   sqlalchemy==2.0.25
   alembic==1.13.1
   pydantic==2.5.3
   pydantic-settings==2.1.0
   httpx==0.26.0
   feedparser==6.0.10
   python-multipart==0.0.6
   aiosqlite==0.19.0
   ```
3. Create `frontend/package.json` with React, TypeScript, Vite, TailwindCSS dependencies
4. Create `.env.example`:
   ```
   DATABASE_URL=sqlite:///./data/youtube-watcher.db
   BACKEND_HOST=0.0.0.0
   BACKEND_PORT=8000
   ```
5. Create `.gitignore` with appropriate entries
6. Create basic `README.md`

**Human Action**: Review created files, run `git init` if needed.

**Test**: Files exist in correct locations.

**Commit**: `feat: initial project scaffold`

---

### Phase 1B: Docker Setup

**Goal**: Create single-container Docker configuration.

**Tasks**:
1. Create root `Dockerfile` (single container for both frontend and backend):
   ```dockerfile
   # Stage 1: Build frontend
   FROM node:20-alpine AS frontend-builder
   WORKDIR /frontend
   COPY frontend/package*.json ./
   RUN npm ci
   COPY frontend/ ./
   RUN npm run build

   # Stage 2: Production image
   FROM python:3.11-slim
   WORKDIR /app

   # Install Python dependencies
   COPY backend/requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt

   # Copy backend code
   COPY backend/ .

   # Copy built frontend from stage 1
   COPY --from=frontend-builder /frontend/dist ./static

   # Create data directory
   RUN mkdir -p /app/data

   EXPOSE 8000
   CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
   ```

2. Create `docker-compose.yml` (simplified single service):
    ```yaml
    services:
      app:
        build: .
        ports:
          - "8000:8000"
        volumes:
          - ./data:/app/data
        environment:
          - DATABASE_URL=sqlite:///./data/youtube-watcher.db
    ```

3. Create `docker-compose.dev.yml` for development:
    ```yaml
    services:
      backend:
        build:
          context: .
          dockerfile: Dockerfile.dev
        ports:
          - "8000:8000"
        volumes:
          - ./backend:/app
          - ./data:/app/data
        environment:
          - DATABASE_URL=sqlite:///./data/youtube-watcher.db
        command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

      frontend:
        image: node:20-alpine
        working_dir: /app
        ports:
          - "5173:5173"
        volumes:
          - ./frontend:/app
          - /app/node_modules
        command: sh -c "npm install && npm run dev -- --host"
    ```

4. Create `Dockerfile.dev` for backend development:
   ```dockerfile
   FROM python:3.11-slim
   WORKDIR /app
   COPY backend/requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   ```

5. Create minimal `backend/app/main.py` with:
   - Health endpoint at `/api/health`
   - Static file serving for frontend (production)
   ```python
   from fastapi import FastAPI
   from fastapi.staticfiles import StaticFiles
   from fastapi.responses import FileResponse
   import os

   app = FastAPI()

   @app.get("/api/health")
   async def health():
       return {"status": "ok"}

   # Serve static files in production
   if os.path.exists("static"):
       app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")
       
       @app.get("/{full_path:path}")
       async def serve_spa(full_path: str):
           return FileResponse("static/index.html")
   ```

6. Create minimal React app entry point

**Human Action**:
- For production: `docker compose up --build`
- For development: `docker compose -f docker-compose.dev.yml up --build`

**Test**:
- `curl http://localhost:8000/api/health` returns `{"status": "ok"}`
- Production: Frontend loads at `http://localhost:8000`
- Development: Frontend loads at `http://localhost:5173`

**Commit**: `feat: docker configuration with single-container production build`

---

### Phase 2A: Database & Models

**Goal**: Set up SQLAlchemy models and Alembic migrations.

**Tasks**:
1. Create `backend/app/config.py`:
   ```python
   from pydantic_settings import BaseSettings

   class Settings(BaseSettings):
       database_url: str = "sqlite:///./data/youtube-watcher.db"
       
       class Config:
           env_file = ".env"

   settings = Settings()
   ```

2. Create `backend/app/database.py` with async SQLAlchemy setup
3. Create `backend/app/models/channel.py` - Channel SQLAlchemy model
4. Create `backend/app/models/video.py` - Video SQLAlchemy model
5. Initialize Alembic: `alembic init alembic`
6. Configure `alembic/env.py` for async SQLite
7. Create initial migration
8. Update `main.py` to create tables on startup

**Human Action**: Run `docker compose up` and verify database is created.

**Test**: Database file exists at `data/youtube-watcher.db` with correct tables.

**Commit**: `feat: database models and migrations`

---

### Phase 2B: RSS Service

**Goal**: Implement RSS feed parsing and YouTube URL handling.

**Tasks**:
1. Create `backend/app/services/youtube_utils.py`:
   - `extract_channel_id(url: str) -> str` - Extract channel ID from various URL formats
   - `get_rss_url(channel_id: str) -> str` - Build RSS feed URL
   - `extract_video_id(url: str) -> str` - Extract video ID from YouTube URL
   - `get_video_url(video_id: str) -> str` - Build watch URL

2. Create `backend/app/services/rss_parser.py`:
   - `fetch_channel_info(channel_id: str) -> ChannelInfo` - Get channel name and thumbnail
   - `fetch_videos(rss_url: str, limit: int = 15) -> List[VideoInfo]` - Parse RSS feed
   - `fetch_video_by_id(video_id: str) -> VideoInfo` - Get single video info

**Important**: Handle these YouTube URL formats:
- `https://www.youtube.com/channel/UC...` (direct channel ID)
- `https://www.youtube.com/@username` (handle format)
- `https://www.youtube.com/c/channelname` (custom URL)
- `https://www.youtube.com/user/username` (legacy)

For @username URLs, you'll need to fetch the page and extract the channel ID from meta tags or embedded JSON.

**Human Action**: Test with real YouTube channels.

**Test**: 
```python
# Test channel ID extraction
assert extract_channel_id("https://www.youtube.com/channel/UCxyz") == "UCxyz"

# Test RSS parsing returns video list
videos = await fetch_videos(rss_url, limit=5)
assert len(videos) <= 5
assert all(v.video_id for v in videos)
```

**Commit**: `feat: RSS feed parsing service`

---

### Phase 2C: Channel API

**Goal**: Implement channel management endpoints.

**Tasks**:
1. Create `backend/app/schemas/channel.py`:
   ```python
   class ChannelCreate(BaseModel):
       url: str

   class ChannelResponse(BaseModel):
       id: str
       youtube_channel_id: str
       name: str
       thumbnail_url: Optional[str]
       last_checked: Optional[datetime]
       video_count: int  # Count of inbox + saved videos
   ```

2. Create `backend/app/routers/channels.py`:
   - `GET /api/channels` - List all channels with video counts
   - `POST /api/channels` - Add channel, fetch last 15 videos as inbox
   - `DELETE /api/channels/{id}` - Remove channel and its videos
   - `POST /api/channels/{id}/refresh` - Check for new videos
   - `POST /api/channels/refresh-all` - Refresh all channels

3. Register router in `main.py`

**Logic for adding a channel**:
1. Extract channel ID from URL
2. Check if channel already exists (return error if so)
3. Fetch channel info (name, thumbnail)
4. Fetch last 15 videos from RSS
5. Create channel record
6. Create video records with status='inbox'
7. Return channel with video count

**Logic for refresh**:
1. Fetch current RSS feed
2. Compare with last_video_id
3. Add any new videos with status='inbox'
4. Update last_checked and last_video_id

**Human Action**: Test endpoints with Swagger UI at `http://localhost:8000/docs`

**Test**: 
- Add a channel, verify 15 videos created
- Refresh should return 0 new videos (assuming no new uploads)
- Delete channel removes all associated videos

**Commit**: `feat: channel management API`

---

### Phase 2D: Video API

**Goal**: Implement video management endpoints.

**Tasks**:
1. Create `backend/app/schemas/video.py`:
   ```python
   class VideoResponse(BaseModel):
       id: str
       youtube_video_id: str
       channel_id: Optional[str]
       channel_name: Optional[str]
       title: str
       description: Optional[str]
       thumbnail_url: Optional[str]
       video_url: str
       published_at: datetime
       status: str
       saved_at: Optional[datetime]

   class VideoFromUrl(BaseModel):
       url: str

   class BulkVideoAction(BaseModel):
       video_ids: List[str]
   ```

2. Create `backend/app/routers/videos.py`:
   - `GET /api/videos/inbox` - Get all inbox videos
   - `GET /api/videos/saved` - Get saved videos with query params:
     - `channel_id` - Filter by channel
     - `sort_by` - 'published_at' or 'saved_at'
     - `order` - 'asc' or 'desc'
   - `POST /api/videos/{id}/save` - Move to saved
   - `POST /api/videos/{id}/discard` - Move to discarded
   - `POST /api/videos/bulk-save` - Bulk save
   - `POST /api/videos/bulk-discard` - Bulk discard
   - `POST /api/videos/from-url` - Add video from URL
   - `DELETE /api/videos/{id}` - Remove video

3. Register router in `main.py`

**Logic for from-url**:
1. Extract video ID from URL
2. Check if video already exists (return existing if so)
3. Fetch video info from RSS/oEmbed
4. Create video with status='saved' and saved_at=now
5. If video's channel exists, link it; otherwise channel_id=null

**Human Action**: Test all endpoints with Swagger UI.

**Test**:
- Save video, verify status changes
- Discard video, verify status changes
- Bulk operations work correctly
- Filter and sort work correctly

**Commit**: `feat: video management API`

---

### Phase 3A: Frontend Scaffold

**Goal**: Set up React application with routing and layout.

**Tasks**:
1. Initialize Vite React TypeScript project (if not already)
2. Install dependencies:
   ```bash
   npm install react-router-dom @tanstack/react-query axios
   npm install -D tailwindcss postcss autoprefixer
   npx tailwindcss init -p
   ```

3. Configure TailwindCSS in `tailwind.config.js`
4. Set up `index.css` with Tailwind directives
5. Create `src/types/index.ts` with TypeScript interfaces
6. Create layout components:
   - `Header.tsx` - App title, "Add URL" button
   - `Navigation.tsx` - Tab navigation (Inbox, Saved, Channels)
7. Create `App.tsx` with React Router setup
8. Create placeholder pages:
   - `Inbox.tsx`
   - `Saved.tsx`
   - `Channels.tsx`

**Human Action**: Verify app loads and navigation works (use dev mode).

**Test**: Can navigate between all three pages.

**Commit**: `feat: frontend scaffold with routing`

---

### Phase 3B: API Client

**Goal**: Create TypeScript API client for backend communication.

**Tasks**:
1. Create `src/api/client.ts`:
   ```typescript
   import axios from 'axios';
   
   const api = axios.create({
     baseURL: '/api',
   });
   
   export const channelsApi = {
     list: () => api.get('/channels'),
     create: (url: string) => api.post('/channels', { url }),
     delete: (id: string) => api.delete(`/channels/${id}`),
     refresh: (id: string) => api.post(`/channels/${id}/refresh`),
     refreshAll: () => api.post('/channels/refresh-all'),
   };
   
   export const videosApi = {
     getInbox: () => api.get('/videos/inbox'),
     getSaved: (params: SavedVideosParams) => api.get('/videos/saved', { params }),
     save: (id: string) => api.post(`/videos/${id}/save`),
     discard: (id: string) => api.post(`/videos/${id}/discard`),
     bulkSave: (ids: string[]) => api.post('/videos/bulk-save', { video_ids: ids }),
     bulkDiscard: (ids: string[]) => api.post('/videos/bulk-discard', { video_ids: ids }),
     fromUrl: (url: string) => api.post('/videos/from-url', { url }),
     delete: (id: string) => api.delete(`/videos/${id}`),
   };
   ```

2. Create React Query hooks:
   - `src/hooks/useChannels.ts`
   - `src/hooks/useVideos.ts`

3. Set up QueryClientProvider in `main.tsx`

4. Configure Vite proxy in `vite.config.ts` (for development mode):
   ```typescript
   export default defineConfig({
     server: {
       host: '0.0.0.0',
       proxy: {
         '/api': {
           target: 'http://localhost:8000',
           changeOrigin: true,
         },
       },
     },
   });
   ```

**Note**: In production (single container), no proxy is needed since FastAPI serves both API and frontend from the same origin.

**Human Action**: Test API calls work through browser dev tools.

**Test**: API calls succeed and return expected data.

**Commit**: `feat: TypeScript API client`

---

### Phase 3C: Channel Management UI

**Goal**: Complete channels page with add/delete functionality.

**Tasks**:
1. Create `src/components/common/Button.tsx`
2. Create `src/components/common/Modal.tsx`
3. Create `src/components/common/LoadingSpinner.tsx`
4. Create `src/components/channel/ChannelCard.tsx`:
   - Display thumbnail, name, video count
   - Delete button with confirmation
5. Create `src/components/channel/ChannelList.tsx`
6. Create `src/components/channel/AddChannelModal.tsx`:
   - Input for YouTube URL
   - Submit button
   - Loading state
   - Error display
7. Implement `src/pages/Channels.tsx`:
   - Add channel button opens modal
   - Display channel list
   - Handle empty state

**Human Action**: Test adding and removing channels.

**Test**:
- Add channel via modal
- Channel appears in list with correct info
- Delete channel removes it from list

**Commit**: `feat: channel management UI`

---

### Phase 4A: Inbox Page

**Goal**: Implement video inbox with save/discard actions.

**Tasks**:
1. Create `src/components/video/VideoCard.tsx`:
   - Thumbnail (clickable to open YouTube)
   - Title, channel name, publish date
   - Save and Discard buttons
2. Create `src/components/video/VideoList.tsx`
3. Implement `src/pages/Inbox.tsx`:
   - Refresh button (calls refresh-all)
   - Video list display
   - Bulk action buttons (Save All, Discard All)
   - Empty state when no videos
   - Loading state during refresh

**Human Action**: Test inbox workflow with real channels.

**Test**:
- Videos display correctly
- Save moves video out of inbox
- Discard moves video out of inbox
- Bulk actions work correctly
- Refresh finds new videos (if any)

**Commit**: `feat: inbox page with video triage`

---

### Phase 4B: Saved Videos Page

**Goal**: Implement saved videos with filtering and sorting.

**Tasks**:
1. Add filter dropdown to select channel (or "All Channels")
2. Add sort dropdown:
   - Published Date (newest first)
   - Published Date (oldest first)
   - Saved Date (newest first)
   - Saved Date (oldest first)
3. Display saved videos using VideoCard (modified for saved context)
4. Add "Remove" action to remove from saved
5. Add "Watch" button that opens video in new tab
6. Implement empty state

**Human Action**: Test filtering and sorting.

**Test**:
- Filter by channel works
- Sorting works correctly
- Remove button works

**Commit**: `feat: saved videos page with filtering`

---

### Phase 5: Direct URL Save

**Goal**: Add ability to save any YouTube video by URL.

**Tasks**:
1. Add "Add URL" button to header (visible on all pages)
2. Create `AddVideoModal.tsx`:
   - Input for YouTube URL
   - Submit button
   - Loading and error states
3. Connect to `POST /api/videos/from-url`
4. After success, navigate to Saved page or show confirmation

**Human Action**: Test with various YouTube URL formats.

**Test**:
- Paste URL, video is saved
- Video appears in Saved list
- Works with different URL formats

**Commit**: `feat: direct URL save feature`

---

### Phase 6: Polish

**Goal**: Add final polish, error handling, and documentation.

**Tasks**:
1. Add consistent loading states across all pages
2. Add error boundaries and error displays
3. Add confirmation dialogs for destructive actions
4. Improve empty states with helpful messages
5. Add toast notifications for actions
6. Review and improve responsive design
7. Update README.md with:
   - Features list
   - Installation instructions
   - Usage guide
   - Screenshots
8. Update agents.md with final project state
9. Manual testing of complete workflow

**Human Action**: Full manual test of all features.

**Test**: Complete user workflow works without errors.

**Commit**: `feat: polish and documentation`

**Tag**: `v1.0.0`

---

## Testing Guidelines

### Backend Testing

For each backend phase, verify:
1. Endpoints return correct status codes
2. Response schemas match expected format
3. Database state changes correctly
4. Error cases return appropriate errors

Use Swagger UI at `http://localhost:8000/docs` for manual testing.

### Frontend Testing

For each frontend phase, verify:
1. Components render correctly
2. User interactions trigger expected behavior
3. Loading states display appropriately
4. Errors are handled gracefully

### Integration Testing

Before each commit:
1. Restart containers: `docker compose down && docker compose up --build`
2. Verify database persists across restarts
3. Test complete user workflows

---

## Git Workflow

### Commit Message Format

```
type: description

[optional body]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `refactor`: Code refactoring
- `docs`: Documentation
- `chore`: Maintenance tasks

### After Each Phase

1. Test all functionality added in the phase
2. Verify no regressions in existing functionality
3. Stage changes: `git add .`
4. Commit with descriptive message
5. Tag milestone releases: `git tag v0.x.x`

---

## Common Pitfalls

### SQLite with Async

SQLite requires special handling for async operations. Use `aiosqlite` and configure SQLAlchemy with:
```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

engine = create_async_engine("sqlite+aiosqlite:///./data/youtube-watcher.db")
```

### YouTube URL Parsing

The `@username` format requires fetching the page to get the channel ID. Consider:
1. Fetch the page with httpx
2. Look for `channel_id` in the page content or meta tags
3. Cache results to avoid repeated fetches

### Docker Volume Permissions

Ensure the `data/` directory has correct permissions:
```bash
mkdir -p data
chmod 777 data
```

### CORS Configuration

For development mode (separate frontend dev server), configure CORS in FastAPI:
```python
from fastapi.middleware.cors import CORSMiddleware
import os

# Only add CORS in development
if os.getenv("ENV", "production") == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_methods=["*"],
        allow_headers=["*"],
    )
```

**Note**: In production (single container), CORS is not needed since frontend and API are served from the same origin.

### Vite Proxy (Development Only)

The Vite dev server proxy is only needed during development:
```typescript
// vite.config.ts
export default defineConfig({
  server: {
    host: '0.0.0.0',
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});
```

### Static File Serving in FastAPI

For production, FastAPI serves the built frontend:
```python
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

app = FastAPI()

# Register API routes first (with /api prefix)
app.include_router(channels_router, prefix="/api")
app.include_router(videos_router, prefix="/api")

# Serve static files in production
if os.path.exists("static"):
    # Serve assets (JS, CSS, images)
    app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")
    
    # Catch-all route for SPA - must be last
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Return index.html for any non-API, non-asset route
        return FileResponse("static/index.html")
```

---

## Development vs Production

| Aspect | Development | Production |
|--------|-------------|------------|
| Command | `docker compose -f docker-compose.dev.yml up` | `docker compose up` |
| Frontend | Vite dev server on :5173 | Static files via FastAPI |
| Hot Reload | Yes (both frontend & backend) | No |
| Containers | 2 (backend + frontend) | 1 (combined) |
| URL | Frontend: :5173, API: :8000 | Everything: :8000 |

---

## Summary

This plan breaks development into 12 small, testable phases. Each phase:
- Has clear deliverables
- Can be tested independently
- Results in a working (if incomplete) application
- Is saved to git before proceeding

**Key Architecture Points:**
- Single container in production (FastAPI serves frontend + API)
- Two containers in development (for hot reload)
- SQLite database persisted via Docker volume
- No external dependencies (no API keys, no separate DB server)

Follow phases in order. Do not skip ahead. Test thoroughly before committing.