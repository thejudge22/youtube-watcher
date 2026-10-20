# Backend Improvements — Verified Spec (2026-10-20)

This is the spec for [2026-10-20-backend-improvements-implementation.md](2026-10-20-backend-improvements-implementation.md). Every finding was re-checked against the code at `63ae617`. Items marked **(probed)** were reproduced in a scratch copy, not just read.

Baseline: `pytest -m "not integration"` passes 52 tests with no network; the full suite of 68 passes with YouTube access. `pip-audit` finds no known CVEs in the resolved backend dependencies.

## Product rules (decided by Mark, 2026-10-20)

1. **Subscriptions and saved videos are independent.** Only `POST /api/channels` and `POST /api/import-export/import/channels` may create `channels` rows (subscriptions). Saving or importing a video never subscribes.
2. **Unsubscribing:**
   - Saved videos stay saved, keeping their copied `channel_youtube_id`, `channel_name` and `channel_thumbnail_url`. Their `channel_id` link is set to NULL.
   - Inbox videos move to Recently Deleted (`status='discarded'`, `discarded_at=now`, `saved_at=NULL`).
   - Videos that were already discarded are not changed.

## Findings and decisions

### Security
| ID | Finding | Decision |
|----|---------|----------|
| S1 | **Unauthenticated arbitrary file read (probed).** The SPA catch-all in `main.py` does `os.path.join("static", full_path)`. Both `GET /../x` and `GET //etc/hosts` return the file. This exposes the DB and backups, and auth does not apply to this route. | Resolve the path and require it to stay inside `static/`; otherwise serve `index.html`. Unknown `/api/*` paths return 404 (today they return `200 null`). |
| S2 | Playlist import passes any user-supplied URL to yt-dlp, which will fetch arbitrary hosts (server-side request forgery). | Accept only URLs that `extract_playlist_id()` parses, and rebuild the URL as `https://www.youtube.com/playlist?list=<id>`. |
| S3 | **Login:** no attempt limit; PBKDF2 at 100k iterations; the hash runs synchronously in an async handler; the username comparison is not constant-time. | Add a versioned hash format at 600k iterations, `pbkdf2_sha256.<iter>.<salt>.<hash>`, using only `[A-Za-z0-9_.-]` so it is safe in `.env` and compose files. Legacy hashes keep working. Run verification in a thread. Lock an IP out after 10 failures in 15 minutes (HTTP 429). |
| S4 | The JWT secret is regenerated on every restart unless `JWT_SECRET_KEY` is set, which logs everyone out. The `type` claim is never checked. | If `JWT_SECRET_KEY` is set, use it. Otherwise generate a secret once into `data/.jwt_secret` (mode 0600). Require `type == "access"`, `exp` and `iat`. |
| S5 | `/docs`, `/redoc` and `/openapi.json` are public even when auth is enabled. | Disable all three when `AUTH_ENABLED=true`. |
| S6 | No security headers. | Add `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY` and `Referrer-Policy: strict-origin-when-cross-origin`. A CSP is deferred because it needs frontend testing. |
| S7 | **Script injection in the standalone `quickplay.html` (probed in a browser).** Its `escapeHtml` uses `textContent`→`innerHTML`, which doesn't escape quotes. A title like `x" onmouseover="…` injects an attribute, and that page keeps the API key in `localStorage`. Any YouTuber controls their own video titles. URLs are inserted unescaped too. | Escape `& < > " '`. Build the watch URL from `youtube_video_id`, and use a thumbnail only if it is `https://`. |
| S8 | **Stored `javascript:` URLs (probed).** `/import/videos` stores `video_url` verbatim, and `/import/channels` stores `youtube_url` verbatim. React 18 renders both as `href`, so a crafted import file runs script when a link is clicked. IDs aren't validated either; a probe stored `x"><img src=x>` as a video ID. | On import, validate IDs (video `^[A-Za-z0-9_-]{11}$`, channel `^UC[A-Za-z0-9_-]{22}$`) and rebuild URLs from them, ignoring supplied URLs. Add a data migration that normalizes existing rows. Defense in depth: the frontend renders only `http(s)` hrefs. |
| S9 | A non-ASCII `X-API-Key` header makes `secrets.compare_digest` raise `TypeError`, so the request returns 500 instead of 401 (probed). | Compare UTF-8 bytes. |
| S10 | Login fields have no length limit. | `username` ≤ 256 and `password` ≤ 1024 characters. |
| S11 | **Local image builds bake in local files.** `.dockerignore` doesn't exclude `backend/.venv`, `backend/data/` (which holds a real dev DB, `backend/data/youtube-watcher.db`) or nested `.env` files. CI images are clean because those paths are gitignored. | Exclude `**/.venv/`, `backend/data/`, `data/`, `**/.env` and `**/.env.*`. |
| S12 | The PWA service worker caches `GET /api/*` responses for an hour (NetworkFirst) and keeps them after logout. | Delete the `api-cache` on logout and whenever a stored token is found invalid. |
| S13 | With auth disabled (the default), any web page can reach the API through DNS rebinding, and a few no-body POSTs (refresh-all, detect-shorts-batch) are reachable cross-site. | Add an optional `ALLOWED_HOSTS` env var that enables `TrustedHostMiddleware`; `localhost` and `127.0.0.1` are always allowed so the healthcheck keeps working. README: enable auth on any network you don't fully trust. |
| S14 | The workflow token's default permissions apply to the new CI jobs. | Top-level `permissions: contents: read`; the build job keeps its own `packages: write`. |

**Accepted risks (no task):**
- The JWT lives in `localStorage`, so any script injection could read it. S7, S8 and S6 reduce that exposure, and a CSP is deferred.
- `npm audit`'s two high advisories (`form-data`, `follow-redirects`) are in axios's Node HTTP adapter, which the browser bundle doesn't use.

### Correctness
| ID | Finding | Decision |
|----|---------|----------|
| C1 | **On a fresh install, the first add-channel, refresh or import request returns 500 (probed).** `settings_service._get_setting()` inserts and commits the settings row in the middle of a request. The commit expires every loaded ORM object, and the next attribute access raises `MissingGreenlet`. Tests miss this because `conftest.py` uses `expire_on_commit=False` while production uses the default (`True`). | Make `_get_setting()` read-only: return an unsaved defaults object when the row is missing. Make the test session match production. With both changes plus two test fixes, all 68 tests pass (probed). |
| C2 | **Deleting a channel neither unlinks nor discards anything.** SQLite foreign keys are off. **Existing DBs have `ON DELETE CASCADE`** (the SQLite branch of migration `add_channel_info_to_videos` skipped the change to SET NULL). Turning on `PRAGMA foreign_keys` would delete saved videos (probed). The ORM relationship also declares `cascade="all, delete-orphan"`. | **Never turn on `PRAGMA foreign_keys`.** Delete in this order: discard inbox videos, null every `channel_id` pointing at the channel, then delete the channel. Drop the delete cascade from the ORM relationship. |
| C3 | Three video-import paths create subscriptions: `/import/videos`, `/import/video-urls` and `/import/playlist`. | Link `channel_id` only when the channel is already subscribed; never create one. |
| C4 | **Exports and the JSON backup take a saved video's channel from the subscription,** so videos from unsubscribed channels export with no channel info. | Use the video's own copied fields. Build `channel_url` from `channel_youtube_id`. |
| C5 | Database backups copy the live SQLite file byte by byte, which can produce a torn backup. The path comes from an undocumented `DATABASE_PATH` env var and a hard-coded `/app`. | Use `sqlite3.Connection.backup()`. Take the DB path from `settings.database_url`; the backups directory is `<db dir>/backups`. |
| C6 | A failed manual backup never records `failed`. A scheduled refresh records `success` even when every channel failed. | Record the real outcome. For a refresh: `failed` if no channel succeeded; otherwise `success` with an error summary when some failed. Keep the values `success` and `failed`, which the frontend depends on. |
| C7 | A manual refresh and the scheduled refresh can overlap and hit the unique `youtube_video_id` constraint. | Module-level `asyncio.Lock` around both refresh-all and single-channel refresh. |
| C8 | `PUT /api/settings/settings` without `http_timeout` resets it to 10, because the field defaults to 10.0 instead of None. | Make the field optional. |
| C9 | The API returns naive datetimes, which are UTC values with no zone (probed: SQLite drops tzinfo), so browsers treat them as local time. | Serialize response datetimes as UTC with a `Z` suffix. |
| C11 | **Users get logged out about daily in the same browser (reported by Mark).** Tokens nominally last 14 days, but three things cut them short:<br>1. Without `JWT_SECRET_KEY`, every process or container restart invalidates every token (probed: valid before a simulated restart, invalid after).<br>2. The frontend deletes the stored token whenever `/api/auth/verify` fails for *any* reason, including network errors, a server mid-restart, or a 5xx (`AuthContext.tsx`, the `catch` around `verifyToken`).<br>3. Expiry is absolute; the session isn't renewed while it's being used.<br>Mark's production `.env` wasn't inspected: a low `JWT_EXPIRE_HOURS` there would also explain it. | Persist the secret (S4). The frontend drops the token only on a definite `valid: false` or a 4xx from verify; on a network error or 5xx it keeps the token. Sessions slide: `/api/auth/verify` returns a fresh token once the current one is more than 24 hours old, and the frontend re-verifies on load and when the tab becomes visible. Any 401 from a non-auth API call sends the user to the login page. `JWT_EXPIRE_HOURS` (default 336) becomes the inactivity window. |
| C10 | **Versioned Docker images have never been published.** Tags look like `v2026-09-11`, but CI triggers on `v*.*.*`. ghcr.io has only `latest` and `main` (probed), yet the README tells users to pin `:v2026-04-20`. | Trigger on `v*` and add `type=ref,event=tag`. |

### Performance
| ID | Finding | Decision |
|----|---------|----------|
| P1 | yt-dlp `extract_info` is synchronous inside `async def`, so every lookup freezes the server. The "parallel" imports actually run serially. The `timeout` argument is ignored. | Run it via `asyncio.to_thread`, with `socket_timeout` and `extractor_retries=3`. |
| P2 | The tenacity `@retry` on the yt-dlp functions never fires, because `DownloadError` is converted to `ValueError` inside the function. | Remove those two decorators and rely on yt-dlp's own retries. This keeps today's effective behavior. |
| P3 | Imports fetch from YouTube before checking the DB, and fetch channel info once per video. | Look up the DB first, fetch only new IDs, never fetch channel info, and use 4 concurrent fetches. |
| P4 | Refresh runs one SELECT per feed entry, and shorts detection runs once per channel, serially. | One `IN` query per channel, and one batched shorts detection per refresh-all. |
| P5 | A new `httpx.AsyncClient` per request. | One client per batch operation. A single global client was rejected: its cookie jar persists across calls, and it breaks the existing test mocking. |
| P6 | Bulk save and discard re-query each row after commit. | One UPDATE plus one SELECT. |
| P7 | Missing composite indexes. | Add `(status, published_at)`, `(status, saved_at)` and `(status, is_short, published_at)`. SQLite's query plans use them for the QuickPlay, saved and inbox queries (probed). |
| P8 | `create_all` runs on every settings request. | Remove it. |
| P9 | Request sizes are unbounded. | Inbox `limit ≤ 10000` (the frontend sends 10000); bulk `video_ids ≤ 10000`; import channels ≤ 5000; import videos ≤ 100000; import URLs ≤ 1000; batch-detect `video_ids ≤ 10000`. |

### Build and operations
| ID | Finding | Decision |
|----|---------|----------|
| B1 | Every dependency uses `>=`, and SQLAlchemy 2.1 no longer installs `greenlet`, so fresh installs fail. | Switch to `sqlalchemy[asyncio]` and add a hashed universal lock, `backend/requirements.lock`, generated by `uv pip compile` and installed by both Dockerfiles. A trial lock installed cleanly and resolves identically for amd64 and arm64 (probed). |
| B2 | CI never runs tests. | Add backend test and pip-audit jobs plus a frontend typecheck job, and make the image build depend on them. |
| B3 | Docker uses `node:20` (end of life April 2026), Python 3.12, and has no healthcheck. | Move to `node:24-alpine` (also in `docker-compose.dev.yml`) and `python:3.13-slim`, and add a `HEALTHCHECK` on `/api/health`. |
| B4 | Recent yt-dlp releases expect a JS runtime for full YouTube support. The local tests pass only because `deno` is installed on this Mac. | Verify extraction inside the image. If it fails, stop and ask before adding deno (about 100 MB). |
| B5 | The 500 handler uses `print(traceback)`, and the backup scheduler has a bare `except:`. | Use `logger.exception` and `except Exception`. |
| B6 | `VideoResponse` is built inline three times in `videos.py`. | Use `map_video_to_response`. |

## Considered and dropped
- **SQLite WAL / `busy_timeout`:** aiosqlite already passes Python's default 5-second busy timeout. WAL misbehaves on network filesystems and complicates file-level backups.
- **`PRAGMA foreign_keys=ON`:** it would cascade-delete saved videos (C2).
- **One global httpx client:** see P5.
- **Ruff in CI:** there's no lint baseline, so it would mean a large unrelated cleanup.
- **CSP header:** needs browser testing of the PWA and thumbnails.
- **A migration to seed the settings row:** C1's read-only getter makes it unnecessary.

## Out of scope
- Frontend `npm audit`: 6 advisories (2 high) through axios's dependencies (`follow-redirects`, `form-data`).
- An import of 1000 URLs can still run past the frontend's 5-minute timeout. Async import jobs would be a separate feature.
