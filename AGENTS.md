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
| 2026-10-20 | Visual refresh (branch `ui-refresh-slate`): slate theme with one coral accent, desktop sidebar + phone bottom tab bar, flat cards (Save solid, Discard ghost), shared `PageHeader` and segmented toggles, gradients/glows removed, hard-coded colours replaced by theme tokens. All Inbox actions unchanged. |
| 2026-10-20 | Backend hardening: closed a static-file path traversal, login rate limiting and versioned password hashes, persistent JWT secret with sliding sessions, safe import validation, subscriptions independent of saved videos, yt-dlp off the event loop, batched refresh, composite indexes, SQLite backup API, hashed dependency lock, CI test gate. See [plans/backend-improvements.md](plans/backend-improvements.md). |
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

UI/UX improvement ideas (vocabulary, confirmations, Recently Deleted, mobile, view toggles) are tracked in [plans/ui-ux-backlog.md](plans/ui-ux-backlog.md).

Open follow-ups from the 2026-10-20 backend hardening (all minor; see [plans/backend-improvements.md](plans/backend-improvements.md#implementation-record-2026-10-20)):

- A refresh holds the SQLite write lock while it runs Shorts detection over HTTP; after a long gap with many new videos, a save/discard during a scheduled refresh can hit "database is locked".
- `GET /api` (no trailing path) serves `index.html` instead of 404.
- The login rate limiter keeps one in-memory entry per failing IP until that IP returns.
- `create_channel`, video imports and `from-url` insert videos outside `refresh_lock`, so a race with a refresh can still raise an IntegrityError (rare).
- `detect_and_store_shorts` swallows exceptions; a DB error inside it would break the caller's commit.
- Importing more than 1,000 URLs returns a 422; the frontend shows only a generic error.
- Not browser-tested: the frontend keeping the stored token when `/api/auth/verify` fails with a network error or 5xx.
- Frontend `npm audit`: advisories in axios's Node-only dependencies (`form-data`, `follow-redirects`).

## Development Commands

```bash
# Run locally from source (single container, built from this checkout; needs .env)
docker compose -f docker-compose-local.yml up
# Access at http://localhost:38000 (add --build to rebuild after code changes)

# Production mode (pulls the published ghcr.io image)
docker compose up -d
# Access at http://localhost:38000

# Development mode (hot reload for both frontend and backend)
docker compose -f docker-compose.dev.yml up --build
# Frontend: http://localhost:5173
# Backend API: http://localhost:8000

# View logs
docker compose logs -f

# Stop services
docker compose down

# Backend dev environment (once)
cd backend && python3 -m venv .venv
.venv/bin/pip install --require-hashes -r requirements.lock
.venv/bin/pip install -r requirements-dev.txt pip-audit

# Run backend tests (offline; add network access and drop -m to include integration tests)
.venv/bin/python -m pytest -m "not integration"

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
| `docker-compose.yml` | Production compose service mapping (published image) |
| `docker-compose-local.yml` | Local single-container build from source |
| `docker-compose.dev.yml` | Hot-reloaded dev composition |
| [backend/app/main.py](backend/app/main.py) | FastAPI app entrypoint, mounts, and PWA routes |
| [backend/app/auth.py](backend/app/auth.py) | Versioned PBKDF2 hashing, login rate limiter, JWT secret persistence and sliding-session tokens, API key check |
| [backend/app/spa.py](backend/app/spa.py) | Serves the built frontend; `resolve_static_file` confines paths to `static/` |
| [backend/app/services/video_import_service.py](backend/app/services/video_import_service.py) | Shared URL-list/playlist import: DB-first, never subscribes |
| [backend/app/services/channels_service.py](backend/app/services/channels_service.py) | Feed refresh (`refresh_lock`, batched Shorts detection via `detect_and_store_shorts`) |
| [backend/app/services/backup_service.py](backend/app/services/backup_service.py) | JSON and SQLite-backup-API database backups; paths from `DATABASE_URL` |
| [backend/app/schemas/types.py](backend/app/schemas/types.py) | `UTCDateTime`: API datetimes serialized as UTC (`Z`) |
| [backend/requirements.lock](backend/requirements.lock) | Hashed dependency lock installed by both Dockerfiles and CI |
| [backend/tests/factories.py](backend/tests/factories.py) | Test factories (`make_channel`, `make_video`, `reload`) |
| [frontend/src/utils/safeUrl.ts](frontend/src/utils/safeUrl.ts) | `safeExternalUrl`: only http(s) links reach `href` |
| [plans/backend-improvements.md](plans/backend-improvements.md) | 2026-10-20 backend hardening spec, decisions and implementation record |
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
- **Subscriptions vs saved videos:** Only `POST /api/channels` and `POST /api/import-export/import/channels` create channels (subscriptions). Saving or importing a video never subscribes. Unsubscribing keeps saved videos (unlinked, with their copied channel info) and moves the channel's inbox videos to Recently Deleted.
- **Never enable `PRAGMA foreign_keys`:** existing SQLite databases still declare `ON DELETE CASCADE` on `videos.channel_id`, so enabling it would delete saved videos. Code unlinks videos explicitly instead.
- **Dependencies** are pinned with hashes in `backend/requirements.lock` (see DEVELOPER_GUIDE.md, Updating Dependencies).

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

## Backend Hardening (2026-10-20)
* Spec, decisions and implementation record: [plans/backend-improvements.md](plans/backend-improvements.md); task-by-task plan: [plans/2026-10-20-backend-improvements-implementation.md](plans/2026-10-20-backend-improvements-implementation.md). Merged to local `main` as of 2026-10-20 (head `dde0bbb`); check `git status` before assuming it is on GitHub.
* **Security:** SPA path traversal fixed (`app/spa.py`); playlist URLs rebuilt from the playlist ID (no SSRF); imported video/channel IDs validated and URLs rebuilt, with migration `d4e5f6a7b8c9` normalizing stored URLs; frontend only renders http(s) links; `quickplay.html` escapes quotes; login rate limit (10 failures/IP/15 min, counted before hashing); PBKDF2 at 600k with versioned hashes (legacy still verify); JWT secret persisted to `data/.jwt_secret`; `/docs` hidden when auth is on; security headers; optional `ALLOWED_HOSTS`.
* **Sessions:** `/api/auth/verify` returns a renewed token once the current one is a day old; the frontend keeps the token on network errors and returns to login on any non-auth 401. This fixed daily logouts (caused by the per-restart JWT secret).
* **Subscriptions vs saved videos:** imports never create channels; unsubscribing discards inbox videos, keeps saved ones and backfills their copied channel info; exports and JSON backups use the video's own channel fields.
* **Correctness:** fresh installs no longer 500 (settings getters are read-only); tests use production's `expire_on_commit=True` (read ids before committing in tests; use `tests/factories.reload`); backups use SQLite's backup API; refresh/backup status reflects failures; partial settings updates keep other fields; API datetimes are UTC.
* **Performance:** yt-dlp runs in a worker thread; imports check the DB before fetching; refresh uses one `IN` query per channel, one Shorts batch per run and one HTTP client per batch; bulk save/discard is one UPDATE; composite indexes (migration `c3d4e5f6a7b8`); request size caps; JSON import lookups are chunked under SQLite's variable limit.
* **Build/CI:** `backend/requirements.lock` (hashed, from `uv pip compile`); Python 3.13 and Node 24 images with a healthcheck; CI runs offline pytest, pip-audit and frontend tsc/lint before building; `v*` tags publish versioned images.
