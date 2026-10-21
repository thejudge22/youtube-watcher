# Native Clients

Two native apps use this API alongside the web app. Both live in private repositories, separate from this one.

| App | Platforms |
|---|---|
| YTW-QuickPlay | macOS, iPhone, iPad (SwiftUI) |
| YTW-Quickplay-Android | Android (Jetpack Compose) |

They cover QuickPlay (the oldest 50 saved videos and Shorts, played as a YouTube playlist), the Inbox (save, discard, bulk actions, refresh channels) and Add URL. They are first-class clients: a change that breaks them is a regression, just like one that breaks the web app.

The full contract, with response fixtures, is kept with the apps' planning docs (`QuickPlayNativeAppsPlans/API_SPEC.md` in the QuickPlayClient folder on the dev machine). [backend/tests/test_native_client_contract.py](../backend/tests/test_native_client_contract.py) enforces the parts listed below.

## What they call

All requests send `Accept: application/json`. When auth is on, they also send `X-API-Key`. They never use the JWT login.

| Endpoint | Exact request | They rely on |
|---|---|---|
| `GET /api/health` | — | 200 without auth; `version` and `api_version` as strings |
| `GET /api/videos/saved` | `is_short=true\|false&sort_by=published_at&order=asc&limit=50&offset=0` | `PaginatedVideosResponse` |
| `GET /api/videos/saved` | `limit=1` | Setup and Settings use it to check the API key (401 = wrong key) |
| `GET /api/videos/inbox` | `limit=10000&offset=0` | A plain `Video[]`, oldest first; **10000 is the current cap** |
| `POST /api/videos/{id}/save`, `/discard` | — | 200 + `Video` |
| `POST /api/videos/bulk-save`, `/bulk-discard` | `{"video_ids": [...]}` | 200 + `Video[]`. QuickPlay Remove uses bulk-discard; its Undo uses bulk-save |
| `POST /api/videos/from-url` | `{"url": "..."}` | 201 or 200 + `Video` |
| `POST /api/channels/refresh-all` | — | 200 + `{channels_refreshed, new_videos_found, errors}` |
| `GET /api/auto-refresh/status` | — | Optional: `auto_refresh_enabled`, `last_refresh_at`, `last_refresh_status` for an "Auto-refreshed … ago" line |
| `DELETE /api/videos/{id}` | — | 204. Only app versions before 1.1 call it. Keep it until those installs are gone |

`Video` fields they decode:
- Non-null: `id`, `youtube_video_id`, `title`, `video_url`, `published_at`, `status`, `is_short`.
- Nullable: `channel_id`, `channel_youtube_id`, `channel_name`, `channel_thumbnail_url`, `description`, `thumbnail_url`, `saved_at`, `discarded_at`, `is_short_detected_at`.

Errors are read from the envelope (`error.code`, `error.message`). A `400` with a `text/plain` body is taken to mean the host is not on `ALLOWED_HOSTS`.

## Compatibility rules

When you change `backend/app/routers/`, `backend/app/schemas/`, `backend/app/auth.py`, `backend/app/main.py` or `backend/app/error_handlers.py`:

1. **Additive only.** Don't remove or rename the fields above, and don't make a non-null field nullable.
2. **Keep the status codes**, including from-url's 201/200 and DELETE's 204.
3. **Don't lower** the inbox `limit` cap below 10000 or the saved `limit` cap below 50.
4. **Keep `X-API-Key`** accepted on these endpoints, and keep `/api/health` and `/api/auth/status` open.
5. **Datetimes stay ISO 8601 UTC.** The apps parse `published_at`.
6. **Keep the error envelope** and `ALLOWED_HOSTS`' plain-text 400. The apps map both to messages.
7. **Breaking change?** Bump `api_version` in `/api/health`, keep the old behavior for a release, and update the apps first. The apps warn when `api_version` isn't `"1"`.
8. **Changing what a shared screen does** (QuickPlay, Inbox, Add URL) in the web app is a parity change. Note it in the native plans even if the API doesn't change.

`pytest tests/test_native_client_contract.py` checks rules 1–5 and the error envelope. It runs in the default offline suite and in CI. If it fails, the change breaks installed apps: follow rule 7 rather than editing the test.

## Server settings that affect the apps

- `AUTH_ENABLED=true` needs `API_KEY` set, or the apps can't authenticate.
- If `ALLOWED_HOSTS` is set, it must include the host name or IP the apps use. Otherwise the apps show "The server rejected this address".
- Plain HTTP works: the Apple apps allow arbitrary loads, and Android allows cleartext.

## History

| Date | Change | Effect on the apps |
|---|---|---|
| 2026-10-21 | Apps 1.1 | Remove goes to Recently Deleted (bulk-discard) with Undo. Play All is removed and Play is per list, matching the web app. The API key is checked at Setup. Clear error messages. iPhone support. |
| 2026-10-21 | Native-client contract test | Backend changes that would break the apps now fail CI |
| 2026-10-20 | Datetimes serialized as UTC with `Z` | Fixed blank publish dates in the Apple app (pre-1.1) |
| 2026-10-20 | `ALLOWED_HOSTS` added | The apps' host must be on the list when it's set |
| 2026-09-11 | Web QuickPlay Remove switched to `bulk-discard` | The apps matched it in 1.1 |
