# YouTube-Watcher

A self-hosted web app for managing YouTube content discovery. Monitor channels via RSS feeds, triage new videos in an inbox, and maintain a personal watch-later list.

<img width="1280" height="714" alt="image" src="https://github.com/user-attachments/assets/f709ce63-3f6b-43c6-852f-5f291a81ec89" />

## Features

- **Channel Management** - Track YouTube channels via RSS feeds (no API key needed)
- **Video Inbox** - Review new videos with save/discard options
- **Saved Library** - Filter, sort, and bulk-manage saved videos
- **Play as Playlist** - Generate a YouTube playlist from selected videos
- **Import/Export** - Backup and restore channels and saved videos
- **Optional Authentication** - Secure your instance with login or API keys
- **PWA Support** - Install as a Progressive Web App

## Installation

Requires Docker, Docker Compose, and Git.

### Quick Start

1. Create `docker-compose.yml`:

```yaml
services:
  app:
    image: ghcr.io/thejudge22/youtube-watcher:latest
    ports:
      - "38000:8000"
    volumes:
      - ./data:/app/data
    env_file:
      - .env
    user: "1000:1000"
    restart: unless-stopped
```

2. Copy `.env.example` to `.env`
3. Start: `docker compose up -d`
4. Open http://localhost:38000

Data is persisted in `./data/youtube-watcher.db` via the volume mount.

> The `:latest` tag builds from every commit. For a static version, use a release tag like `:v1.13.0`.

### Development

```bash
git clone https://github.com/thejudge22/youtube-watcher.git
cd youtube-watcher
docker compose -f docker-compose-local.yml up --build
```

## Authentication

Authentication is disabled by default. Enable it when exposing to public networks.

### Username/Password Login

Generate a password hash and update your `.env`:

```bash
./scripts/generate-password-hash.sh
```

Set in `.env`:
```ini
AUTH_ENABLED=true
AUTH_USERNAME=admin
AUTH_PASSWORD_HASH=<hash from script>
```

Sessions last 14 days by default (configurable via `JWT_EXPIRE_HOURS`).

### API Key Access

For programmatic access to protected endpoints, generate an API key:

```bash
./scripts/generate-api-key.sh
```

Set in `.env`:
```ini
API_KEY=<key from script>
```

Include the header on API requests:

```bash
curl http://localhost:38000/api/channels \
  -H "X-API-Key: <your-api-key>"
```

## Usage

**Adding Channels** - Navigate to Channels, click Add Channel, and paste a YouTube URL. Supports `@handle`, channel ID, custom URLs, and direct video URLs.

**Inbox** - Review new videos, save or discard individually, or use Save All / Discard All.

**Saved Videos** - Filter by channel, sort by date, switch between Large/Compact/List views, select multiple for bulk operations, or play as a YouTube playlist.

**Direct URL Save** - Click the **+** button to add any YouTube URL directly to your saved list.

**Settings** - Configure HTTP timeout, import/export data, and manage recently deleted videos.

## Supported URL Formats

| Type | Example |
|------|---------|
| Channel Handle | `https://youtube.com/@JoshuaWeissman` |
| Channel ID | `https://youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw` |
| Custom URL | `https://youtube.com/c/SomeChannel` |
| Video | `https://youtube.com/watch?v=dQw4w9WgXcQ` |
| Shorts | `https://youtube.com/shorts/mccyHdidiG8` |
| Short URL | `https://youtu.be/dQw4w9WgXcQ` |

## API Documentation

Interactive docs available at `/docs` when the app is running.

## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python + FastAPI |
| Frontend | React + TypeScript + TailwindCSS |
| Database | SQLite |
| Deployment | Docker |

## License

MIT
