# YouTube-Watcher - AI Agent Context

> This file provides context for AI pair programmers working on this project.
> Keep it updated with significant changes and current project state.

## Project Overview

YouTube-Watcher is a self-hosted, Docker-based web application for managing YouTube content discovery. It monitors YouTube channels via RSS feeds, presents new videos in an inbox-style interface for triage, and maintains a personal "watch later" list.

**Key Characteristics:**
- Single-user application (no authentication)
- Docker-based deployment
- YouTube RSS feeds for data (no API key required)
- User-initiated video checks (no scheduled tasks)

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
| 2026-01-12 | Initial project setup - created development plan and agents.md |
| 2026-01-12 | Completed Phase 1 & 2. Implemented full testing suite (45 tests). Added support for Shorts and Handle URLs. |
| 2026-01-12 | Completed Phases 3-6. Full frontend implementation with React, TypeScript, and TailwindCSS. Updated README with documentation. |

## Architecture Notes

See `plans/development-plan.md` for full architecture details.

**Quick Summary:**
- Single Docker container in production (FastAPI serves API + static frontend)
- Two containers in development (for hot reload)
- SQLite database stored in `./data/youtube-watcher.db`
- REST API at `/api/*` endpoints
- Frontend served as static files from same FastAPI server

## Known Issues & TODOs

No known issues - project is complete.

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

# API Docs (both modes)
# http://localhost:8000/docs
```

## Key Files

| File | Purpose |
|------|---------|
| `plans/development-plan.md` | High-level development plan |
| `agents.md` | This file - AI context |
| `Dockerfile` | Single-container production build |
| `docker-compose.yml` | Production deployment |
| `docker-compose.dev.yml` | Development with hot reload |
| `backend/app/main.py` | FastAPI app - serves API + static files |
| `frontend/src/App.tsx` | React application entry point |
| `README.md` | User-facing documentation |

## Core Features Reference

1. **Channel Management** - Add/remove YouTube channels to track
2. **Video Inbox** - Triage new videos (save or discard)
3. **Saved Videos** - View saved videos with filtering/sorting
4. **Direct URL Save** - Paste any YouTube URL to save directly
5. **Bulk Actions** - Save/discard all inbox videos at once

## Conventions

- All dates in ISO 8601 format
- API endpoints prefixed with `/api/`
- Video status enum: `inbox`, `saved`, `discarded`
- **Testing:** Always run existing tests and verify all features work after implementing a change.

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

*   The Docker Compose command has been updated from the legacy `docker-compose` (with a hyphen) to `docker compose` (with a space) to align with modern Docker CLI syntax. All documentation and scripts should reflect this change.
*   The top-level `version` tag has been removed from `docker-compose.yml` and `docker-compose.dev.yml` as it is obsolete in the current Docker Compose specification.
- Use UUID for all primary keys

## Phase 6: Polish (2026-01-12)

Completed UI/UX polish:
- Added loading spinners to all pages
- Implemented error handling with visible error messages
- Added empty state messages with helpful text for Inbox, Saved, and Channels pages

Updated documentation:
- Complete README.md with features list, installation instructions, usage guide
- Updated agents.md to reflect completed project state