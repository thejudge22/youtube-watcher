# YouTube-Watcher

A self-hosted, Docker-based web application for managing YouTube content discovery. Monitor YouTube channels via RSS feeds, triage new videos in an inbox-style interface, and maintain a personal watch later list.

<img width="1280" height="714" alt="image" src="https://github.com/user-attachments/assets/f709ce63-3f6b-43c6-852f-5f291a81ec89" />


## Features

- **Channel Management** - Add and manage YouTube channels to track via RSS feeds
- **Video Inbox** - Review new videos from your channels with save/discard options
- **Bulk Actions** - Save or discard all videos in your inbox with one click
- **Saved Videos Library** - View and manage your saved videos with filtering and sorting
- **Video Selection Mode** - Select multiple saved videos for bulk operations
- **Play as Playlist** - Generate a YouTube playlist from selected videos (up to 50)
- **Multiple View Modes** - Choose between Large, Compact, or List view layouts for videos
- **Channel List View** - Toggle between grid and list views for channels
- **Bulk Remove** - Remove multiple selected videos at once
- **Recently Deleted** - Restore accidentally deleted videos within a retention period
- **Direct URL Save** - Add any YouTube video URL directly to your saved list
- **YouTube Shorts Support** - Full support for YouTube Shorts URLs
- **Configurable Timeouts** - Adjust HTTP request timeout via Settings page
- **Import/Export** - Backup and restore your channels and saved videos
- **RSS-based** - No YouTube API key required, uses RSS feeds
- **Self-hosted** - Your data stays on your server
- **Responsive Design** - Works on desktop and mobile devices

## Installation

### Prerequisites

- Docker and Docker Compose
- Git

#### A note about docker images
The ghcr.io/thejudge22/youtube-watcher:latest tag always builds from every commit.  Use that if you want the most up to date docker image.  If you want a static version, tag your docker image like this:  ghcr.io/thejudge22/youtube-watcher:1.10

#### Quick Start with Pre-built Images

1. Create a `docker-compose.yml` file:
```yaml
services:
  youtube-watcher:
    image: ghcr.io/thejudge22/youtube-watcher:latest
    ports:
      - "38000:8000"
    volumes:
      - ./data:/app/data
    environment:
      - DATABASE_URL=sqlite+aiosqlite:///./data/youtube-watcher.db
    user: "1000:1000"
    restart: unless-stopped
```

2. Create the data directory:
```bash
mkdir -p data
```

3. Start the application:
```bash
docker compose up -d
```

4. Access the application at http://localhost:38000

### Development Mode

For development or local builds, clone the repo and run:

```bash
docker compose -f docker-compose-local.yml up --build
```

- Access the application at http://localhost:38000
- API Documentation: http://localhost:38000/docs



#### Data Persistence

The application uses a volume mount to persist data:
```yaml
volumes:
  - ./data:/app/data
```

This ensures your database and application data persists across container updates and restarts. The SQLite database file is stored at `./data/youtube-watcher.db`.




## Usage

### Settings

The **Settings** page allows you to configure application preferences:

- **HTTP Request Timeout** - Adjust how long to wait for YouTube/RSS API responses (1-300 seconds, default: 10). Increase this if you experience timeout errors on slow connections.
- **Import/Export** - Backup your channels and saved videos to JSON files, or restore from previous backups
- **Data Management** - Remove all saved videos or purge recently deleted videos

### Adding Channels

1. Navigate to the **Channels** page
2. Click **Add Channel**
3. Paste a YouTube channel URL (supports `@handle`, channel ID, and custom URL formats)
4. Click **Add** to start tracking

**Channel View Modes:**
- Toggle between **Grid** and **List** views using the buttons in the header
- Grid view shows channels as cards with thumbnails
- List view shows channels in a table with more details
- Your view preference is saved automatically

**Channel Actions:**
- Click the **Refresh** button to check for new videos from a specific channel
- Click the **Delete** button to remove a channel and all its videos

### Managing Videos

**Inbox Tab:**
- Review new videos from your subscribed channels
- Click **Save** to add to your saved list
- Click **Discard** to remove from inbox
- Use **Save All** or **Discard All** for bulk actions
- Click **Refresh** to check for new videos

**Saved Videos Tab:**
- View all your saved videos
- Filter by channel
- Sort by published date or saved date
- Switch between Large, Compact, and List view modes
- Select multiple videos for bulk operations
- Play selected videos as a YouTube playlist (opens in new tab)
- Remove selected videos in bulk
- Click **Remove** to discard a single saved video
- View and restore recently deleted videos

**Direct URL:**
- Click the **+** button to add any YouTube URL directly to your saved videos

## Supported URL Formats

| Type | Format | Example |
|------|--------|---------|
| Channel Handle | `@username` | `https://www.youtube.com/@JoshuaWeissman` |
| Channel ID | `/channel/UC...` | `https://www.youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw` |
| Custom URL | `/c/username` | `https://www.youtube.com/c/SomeChannel` |
| Video | `/watch?v=...` | `https://www.youtube.com/watch?v=dQw4w9WgXcQ` |
| Shorts | `/shorts/...` | `https://www.youtube.com/shorts/mccyHdidiG8` |
| Short URL | `youtu.be/...` | `https://youtu.be/dQw4w9WgXcQ` |




## API Documentation

API documentation is available at `/docs` when the application is running.



## Tech Stack

| Component | Technology |
|-----------|------------|
| Backend | Python + FastAPI |
| Frontend | React + TypeScript + TailwindCSS |
| Database | SQLite |
| Deployment | Docker |


## License

MIT License - feel free to use and modify for your own purposes.


## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
