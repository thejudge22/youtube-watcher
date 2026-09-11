# YouTube-Watcher - AI Agent Context

> This file provides context for AI pair programmers working on this project.
> Keep it updated with significant changes and current project state.

## Project Overview

YouTube-Watcher is a self-hosted, Docker-based web application for managing YouTube content discovery. It monitors YouTube channels via RSS feeds, presents new videos in an inbox-style interface for triage, and maintains a personal "watch later" list.

**Key Characteristics:**
- **Optional Authentication**: Supports secure instance access via username/password login or API keys.
- **Docker-based deployment**: Deploys as a single-container production image or multi-container development environment.
- **Data Scraping**: Fetches YouTube RSS feeds (no API key required) and scrapes HTML with consent-bypass cookies.
- **Schedulers**: Supports background feed auto-refresh and database backups via `APScheduler`.

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Python + FastAPI |
| Frontend | React + TypeScript + TailwindCSS |
| Database | SQLite |
| Deployment | Single Docker container (FastAPI serves both API + static frontend) |

## Recent Changes

| Date | Change |
|------|--------|
| 2026-09-11 | Added independent QuickPlay batch-removal controls for videos and Shorts; removed items move to Recently Deleted. |
| 2026-05-27 | Created [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) and updated `AGENTS.md` context for future developers/agents. |
| 2026-05-08 | Added PWA Support with Service Worker route overrides, automated scheduled backups, and background feed auto-refresh. |
| 2026-04-20 | Added Optional Authentication (PBKDF2 login + JWT sessions + X-API-Key programmatic access) and YouTube Shorts batch HTTP status detection. |
| 2026-03-15 | Implemented Play as Playlist, touch-drag multi-selection, and channel/video database backup exports. |
| 2026-01-12 | Completed Phase 6 Polish: Added loading states, error boundaries, empty states, and final developer docs. |
| 2026-01-12 | Completed initial phases: channel management, video inbox, saved library, and tests. |

## Architecture Notes

See [plans/development-plan.md](plans/development-plan.md) and [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for full architecture details.

**Quick Summary:**
- Single Docker container in production (FastAPI serves API, background schedulers, and static built frontend files).
- Two containers in development (FastAPI backend + Vite frontend for hot reload).
- SQLite database stored in `./data/youtube-watcher.db`.
- REST API at `/api/*` endpoints.
- Global FastAPI exception handling with standardized `ErrorResponse` JSON outputs.

## Known Issues & TODOs

No known issues - project is complete and fully functional.

## Development Commands

```bash
# Production mode (single container)
docker compose up --build
# Access at http://localhost:8000

# Development mode (hot reload for both frontend and backend)
docker compose -f docker-compose.dev.yml up --build
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000

# View logs
docker compose logs -f

# Stop services
docker compose down

# Run backend tests
cd backend && pytest

# API Docs (both modes)
# http://localhost:8000/docs
```

## Key Files

| File | Purpose |
|------|---------|
| [plans/development-plan.md](plans/development-plan.md) | High-level development plan |
| [AGENTS.md](AGENTS.md) | This file - AI context and project summary |
| [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) | Comprehensive system architecture & onboarding guide |
| `Dockerfile` | Single-container production build |
| `Dockerfile.dev` | Development environment image build |
| `docker-compose.yml` | Production compose service mapping |
| `docker-compose.dev.yml` | Hot-reloaded dev composition |
| [backend/app/main.py](backend/app/main.py) | FastAPI app entrypoint, mounts, and PWA routes |
| [backend/app/auth.py](backend/app/auth.py) | Password hashing, JWT token creation, and API Key middleware |
| [backend/app/services/shorts_detector.py](backend/app/services/shorts_detector.py) | Batch concurrent HTTP-status based Shorts detector |
| [frontend/src/App.tsx](frontend/src/App.tsx) | React application shell and routing entrypoint |
| [frontend/src/context/AuthContext.tsx](frontend/src/context/AuthContext.tsx) | React authentication context provider |
| [README.md](README.md) | User-facing installation and usage guide |

## Core Features Reference

1. **Channel Management** - Add/remove YouTube channels to track (resolves handles, custom, user, and direct ID URLs).
2. **Video Inbox** - Triage new videos (save or discard, bulk save/discard, interval auto-refresh).
3. **Saved Videos** - View saved videos with filtering, sorting, compact/large/list views, and touch-drag multi-select.
4. **Direct URL Save** - Paste any YouTube URL to save directly to the library.
5. **Play as Playlist** - Select videos and play them as a dynamic YouTube playlist (capped at 50 videos).
6. **QuickPlay** - Load the oldest 50 saved videos and Shorts independently, play either batch, or move the displayed batch to Recently Deleted and load the next one.
7. **Scheduled Backups** - Automated JSON data and database gzip backups with configurable schedules and retention periods.
8. **PWA Support** - Add to home screen support on mobile devices.

## Conventions

- All dates in ISO 8601 format.
- API endpoints prefixed with `/api/`.
- Video status enum: `inbox`, `saved`, `discarded`.
- Use UUID for all database primary keys.
- **Version Release Workflow**: Date-based versions (`vYYYY-MM-DD`). Run `./scripts/update_version.sh vYYYY-MM-DD` to sync frontend and API versions, commit the result, create the matching tag, and push the commit and tag.
- **Testing:** Always run pytest on the backend and ensure all test fixtures pass before merging changes.

## Supported YouTube URL Formats

| Type | Format | Example |
|------|--------|---------|
| Channel | Handle | `https://www.youtube.com/@JoshuaWeissman` |
| Channel | ID | `https://www.youtube.com/channel/UC...` |
| Channel | Custom | `https://www.youtube.com/c/SomeChannel` |
| Video | Regular | `https://www.youtube.com/watch?v=gYFZ4HYTsZI` |
| Video | Shorts | `https://www.youtube.com/shorts/mccyHdidiG8` |
| Video | Short URL | `https://youtu.be/VIDEO_ID` |

# Project Development Notes

## Docker Configuration Update (2026-01-12)
* The Docker Compose command has been updated from the legacy `docker-compose` (with a hyphen) to `docker compose` (with a space) to align with modern Docker CLI syntax. All documentation and scripts should reflect this change.
* The top-level `version` tag has been removed from `docker-compose.yml` and `docker-compose.dev.yml` as it is obsolete in the current Docker Compose specification.

## Optional Authentication (2026-04-20)
* Set up a configurable `AUTH_ENABLED` toggle.
* Implemented username/password PBKDF2 hashing, JWT access token issuing, and programmatic header `X-API-Key` checks.

## PWA & APScheduler Support (2026-05-08)
* Registered service worker and manifest custom router routes in FastAPI (`/sw.js`, `/manifest.webmanifest`, `/workbox-{id}.js`) to bypass browser directory constraints.
* Integrated `APScheduler` for automated database backups and channel updates. Added retention-based automatic directory sweeps.

## Agent Guide (2026-05-27)
* Compiled [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) to serve as a comprehensive onboarding agent manual for future developers.

## QuickPlay Batch Removal (2026-09-11)
* Added independent controls for moving the displayed video or Shorts batch to Recently Deleted.
* Each successful removal refreshes only its section with the next oldest batch, if one exists.