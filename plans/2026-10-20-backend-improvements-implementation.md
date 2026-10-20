# Backend Improvements Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix the verified security, correctness, performance and build problems in the YouTube-Watcher backend, and make subscriptions and saved videos fully independent.

**Architecture:** FastAPI with async SQLAlchemy on SQLite; Alembic migrations run at startup. Each task is a small, test-first change to the existing routers and services. Shared logic goes into a service module only where two call sites need it.

**Tech Stack:** Python 3.13, FastAPI, SQLAlchemy 2.1 (async, aiosqlite), Alembic, httpx, yt-dlp, APScheduler, pytest + pytest-asyncio + pytest-mock, React/TypeScript (one small frontend task), Docker, GitHub Actions, uv (lock-file generation only).

**Spec:** [plans/backend-improvements.md](backend-improvements.md). The IDs in brackets (S1, C2, P4, …) refer to its findings.

## Before you start

- Work on a branch: `git checkout -b backend-improvements` from `main`. Commit after every task. Don't push, tag, bump versions or release.
- Run every backend command from `backend/`. One-time setup (until Task 3 adds the lock file):
  ```bash
  cd backend
  python3 -m venv .venv
  .venv/bin/pip install -r requirements-dev.txt greenlet
  .venv/bin/python -m pytest -m "not integration" -q
  ```
  Expected: `52 passed, 16 deselected`.
- "Offline suite" below means `.venv/bin/python -m pytest -m "not integration" -q`. "Full suite" means `.venv/bin/python -m pytest -q`, which needs YouTube access. If you have no network, say so in the task report rather than skipping silently.

## Global Constraints

- Only `POST /api/channels` and `POST /api/import-export/import/channels` may create `Channel` rows. Saving or importing a video never subscribes.
- When a channel is deleted:
  - its saved videos keep `status='saved'`, `channel_youtube_id`, `channel_name` and `channel_thumbnail_url`, with `channel_id` set to NULL;
  - its inbox videos become `status='discarded'`, `discarded_at=now`, `saved_at=NULL`;
  - its already-discarded videos are unchanged.
- **Never execute `PRAGMA foreign_keys=ON`.** Existing production databases have `FOREIGN KEY(channel_id) REFERENCES channels (id) ON DELETE CASCADE`, so turning foreign keys on deletes saved videos.
- Network calls in tests are mocked. A test that needs real network gets `@pytest.mark.integration`.
- After Task 2, test sessions expire ORM objects on commit, as production does. In tests:
  - read any attribute you need (ids etc.) into a local variable **before** `await db_session.commit()`;
  - re-read rows with the `reload` helper from `tests/factories.py` (Task 5);
  - never touch attributes of an object after it was committed.
- Status strings stay `inbox`, `saved` and `discarded`. Refresh and backup status strings stay `success` and `failed`; the frontend compares them literally.
- Add no new runtime dependencies. `uv` is used only to generate the lock file.
- Follow the surrounding code's style: docstrings on public functions, `logger = logging.getLogger(__name__)`, and existing `Issue #NN`-style comments left in place.

## Review Focus

1. **A fresh install with no `settings` row.** The first add-channel, refresh or import must not return 500. Covered by `test_create_channel_invalid_url_on_fresh_db` in Task 2 and the read-only getter tests.
2. **A saved video whose channel is unsubscribed.** It must keep its channel name everywhere: list endpoints, export, JSON backup and re-import. Covered in Tasks 5, 8 and 10.
3. **The same video appearing twice in one import request** (duplicate URLs or JSON entries). It counts as skipped, not as an error or an IntegrityError. Covered in Tasks 9 and 10.
4. **A playlist URL that points somewhere other than YouTube** (e.g. `http://169.254.169.254/`). It is rejected before yt-dlp runs. Covered in Task 9.
5. **A YouTube title, channel name or imported URL containing quotes, HTML or a `javascript:` scheme.** It must render as plain text and never as a live link or attribute. Covered by Task 20 (server rebuilds URLs) and Task 21 (frontend `safeExternalUrl` and the `quickplay.html` escaping check). A related caveat, documented in Task 17: behind a reverse proxy all clients share one IP, so 10 bad logins lock everyone out for 15 minutes.

---

## Phase A — Critical fixes and foundations

### Task 1: Close the static-file path traversal [S1]

**Files:**
- Create: `backend/app/spa.py`
- Modify: `backend/app/main.py:149-191` (the whole `if os.path.exists("static"):` block)
- Test: `backend/tests/test_spa.py`

**Interfaces:**
- Produces: `resolve_static_file(static_dir: Path, requested: str) -> Path | None`, and `register_frontend_routes(app: FastAPI, static_dir: Path) -> None`.

- [ ] **Step 1: Write the failing tests** in `backend/tests/test_spa.py`. Use this raw-ASGI helper: httpx normalizes `..` and `//`, so it can't send these paths.

```python
import asyncio
from pathlib import Path
import pytest
from fastapi import FastAPI
from app.spa import resolve_static_file, register_frontend_routes


async def raw_get(app, path: str) -> tuple[int, bytes]:
    """Send a GET with an un-normalized path straight to the ASGI app."""
    scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": "GET",
             "scheme": "http", "path": path, "raw_path": path.encode(), "query_string": b"",
             "headers": [], "server": ("test", 80), "client": ("test", 1), "root_path": ""}
    messages, sent = [], False

    async def receive():
        nonlocal sent
        if not sent:
            sent = True
            return {"type": "http.request", "body": b"", "more_body": False}
        await asyncio.Event().wait()  # never disconnect

    async def send(message):
        messages.append(message)

    await app(scope, receive, send)
    status = next(m["status"] for m in messages if m["type"] == "http.response.start")
    body = b"".join(m.get("body", b"") for m in messages if m["type"] == "http.response.body")
    return status, body


@pytest.fixture
def site(tmp_path):
    static = tmp_path / "static"
    (static / "assets").mkdir(parents=True)
    (static / "index.html").write_text("SPA")
    (static / "favicon.ico").write_text("ICON")
    (tmp_path / "secret.txt").write_text("SECRET")
    app = FastAPI()
    register_frontend_routes(app, static)
    return tmp_path, static, app
```

The tests:
- `test_resolve_returns_file_inside_static`: `resolve_static_file(static, "favicon.ico") == (static / "favicon.ico").resolve()`
- `test_resolve_rejects_parent_traversal`: `resolve_static_file(static, "../secret.txt") is None`
- `test_resolve_rejects_absolute_path`: `resolve_static_file(static, str(tmp_path / "secret.txt")) is None`
- `test_resolve_rejects_directory_and_missing`: `None` for both `"assets"` and `"nope.txt"`
- `test_resolve_rejects_symlink_escape`: `(static / "link.txt").symlink_to(tmp_path / "secret.txt")`, then expect `None`
- `test_spa_serves_index_for_routes`: `await raw_get(app, "/inbox") == (200, b"SPA")`
- `test_spa_serves_static_file`: `await raw_get(app, "/favicon.ico") == (200, b"ICON")`
- `test_spa_blocks_traversal`: for each of `"/../secret.txt"`, `"//etc/hosts"` and `"/" + str(tmp_path) + "/secret.txt"` (build that one inside the test from the `site` fixture), `await raw_get(app, path) == (200, b"SPA")`
- `test_unknown_api_path_is_404`: `(await raw_get(app, "/api/nope"))[0] == 404`

- [ ] **Step 2: Run the tests to confirm they fail**

Run: `.venv/bin/python -m pytest tests/test_spa.py -q`
Expected: collection error, `ModuleNotFoundError: No module named 'app.spa'`.

- [ ] **Step 3: Implement `backend/app/spa.py`**

`resolve_static_file`:
- resolve `static_dir` and `static_dir / requested` with `Path.resolve()`;
- return `None` on `OSError`/`ValueError`, if the result is not `is_relative_to` the resolved root, or if it is not `is_file()`.

`register_frontend_routes`: move the existing block from `main.py` unchanged — the `/assets` mount, `/sw.js`, `/manifest.webmanifest`, `/workbox-{workbox_id}.js` and the catch-all — with these changes:
- build paths from `static_dir` instead of the literal `"static"`;
- the workbox route resolves `f"workbox-{workbox_id}.js"` through `resolve_static_file`, and returns 404 if that gives `None`;
- the catch-all raises `HTTPException(404)` for `api/...` paths;
- otherwise it serves `resolve_static_file(...)` with the `mimetypes.guess_type` media type when found, else `static_dir / "index.html"`.

- [ ] **Step 4: Wire it into `main.py`**

Replace the whole block with:

```python
if os.path.exists("static"):
    register_frontend_routes(app, Path("static"))
```

Add `from pathlib import Path` and `from .spa import register_frontend_routes`. Remove imports `main.py` no longer uses (`StaticFiles`, `FileResponse`), but keep the module-level `mimetypes.add_type(...)` calls.

- [ ] **Step 5: Run the tests**

Run: `.venv/bin/python -m pytest tests/test_spa.py -q`, then the offline suite.
Expected: all pass; offline suite at 52 + the new tests.

- [ ] **Step 6: Commit**

```bash
git add backend/app/spa.py backend/app/main.py backend/tests/test_spa.py
git commit -m "fix(security): confine SPA file serving to the static directory"
```

### Task 2: Fix the fresh-install 500 and make test sessions match production [C1]

**Files:**
- Modify: `backend/app/services/settings_service.py:11-19` (`_get_setting`)
- Modify: `backend/tests/conftest.py:24-30` (`TestingSessionLocal`)
- Modify: `backend/tests/test_api_videos.py` (`test_list_saved_videos_with_channel_filter`)
- Test: `backend/tests/test_settings_service.py`

**Interfaces:**
- Produces: `_get_setting(db) -> Setting`. It never writes; when the row is missing it returns an unsaved `Setting(id="1", http_timeout=10.0, auto_detect_shorts=True)`.

- [ ] **Step 1: Make the test session expire on commit, like production.** In `conftest.py`, delete the `expire_on_commit=False` argument from `async_sessionmaker(...)`.

- [ ] **Step 2: Run the offline suite to see the failures**

Expected: 2 failures with `MissingGreenlet`:
- `test_create_channel_with_invalid_url` — the real bug;
- `test_list_saved_videos_with_channel_filter` — a stale object in the test itself.

- [ ] **Step 3: Fix the stale test object.** In `test_list_saved_videos_with_channel_filter`:
- add `await db_session.refresh(sample_channel)` right after `await db_session.refresh(channel2)`;
- change the request URL to `"/api/videos/saved?channel_youtube_id=UC-test123"`.

- [ ] **Step 4: Write the failing tests** in `backend/tests/test_settings_service.py`:

```python
from sqlalchemy import select, func
from app.models.setting import Setting
from app.services.settings_service import get_http_timeout, get_auto_detect_shorts


async def test_http_timeout_default_without_row_does_not_write(db_session):
    assert await get_http_timeout(db_session) == 10.0
    assert (await db_session.execute(select(func.count()).select_from(Setting))).scalar_one() == 0


async def test_auto_detect_shorts_default_without_row(db_session):
    assert await get_auto_detect_shorts(db_session) is True


async def test_create_channel_invalid_url_on_fresh_db(client):
    response = await client.post("/api/channels", json={"url": "https://example.com/bad"})
    assert response.status_code == 400
```

- [ ] **Step 5: Run them to confirm they fail**

Run: `.venv/bin/python -m pytest tests/test_settings_service.py -q`
Expected: the row-count assertion fails (1 != 0), and the channel test errors with `MissingGreenlet`.

- [ ] **Step 6: Make `_get_setting` read-only** as described in Interfaces: no `db.add`, no commit.

- [ ] **Step 7: Run the tests**

Run the offline suite, then the full suite if you have network.
Expected: everything passes (68 + new with network; this exact change set was verified to pass the full suite).

- [ ] **Step 8: Commit**

```bash
git add backend/app/services/settings_service.py backend/tests/conftest.py backend/tests/test_api_videos.py backend/tests/test_settings_service.py
git commit -m "fix: stop committing inside settings getters; match production session expiry in tests"
```

### Task 3: Lock dependencies and update the Docker images [B1, B3, B4]

**Files:**
- Modify: `backend/requirements.txt:3`
- Create: `backend/requirements.lock` (generated)
- Modify: `Dockerfile`, `Dockerfile.dev`, `docker-compose.dev.yml:17`, `.dockerignore` [S11]
- Modify: `DEVELOPER_GUIDE.md` (section 4), `AGENTS.md` (Development Commands)

- [ ] **Step 1:** In `requirements.txt`, change `sqlalchemy>=2.0.25` to `sqlalchemy[asyncio]>=2.0.25`.

- [ ] **Step 2: Generate the lock**

```bash
cd backend
uv pip compile requirements.txt --universal --python-version 3.13 --generate-hashes -o requirements.lock
```

Expected: the file contains `greenlet==` and `sqlalchemy==` entries with `--hash=` lines.

- [ ] **Step 3: Rebuild the local venv from the lock and test**

Run these as two separate commands, because pip demands hashes for every requirement once any line has one:

```bash
rm -rf .venv && python3 -m venv .venv
.venv/bin/pip install --require-hashes -r requirements.lock
.venv/bin/pip install -r requirements-dev.txt pip-audit
```

Then run the offline suite (all pass), and:

```bash
.venv/bin/pip-audit --disable-pip --require-hashes -r requirements.lock
```

Expected: `No known vulnerabilities found`.

- [ ] **Step 4: `Dockerfile`**
- `FROM node:20-alpine AS frontend-builder` → `FROM node:24-alpine AS frontend-builder`
- `FROM python:3.12-slim` → `FROM python:3.13-slim`
- Replace `COPY backend/requirements.txt .` and the pip line with:

  ```dockerfile
  COPY backend/requirements.lock .
  RUN pip install --no-cache-dir --require-hashes -r requirements.lock
  ```

- Add this before `CMD`:

  ```dockerfile
  HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
    CMD ["python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=4).status == 200 else 1)"]
  ```

- [ ] **Step 5: `Dockerfile.dev`**
- Change the base image to `python:3.13-slim`.
- Copy `requirements.lock` along with the two existing requirement files.
- Install in two RUN lines: `pip install --no-cache-dir --require-hashes -r requirements.lock`, then `pip install --no-cache-dir -r requirements-dev.txt pip-audit`.

- [ ] **Step 6:** In `docker-compose.dev.yml`, change `image: node:20-alpine` to `image: node:24-alpine`. Then append to `.dockerignore`:

```
# Local environments and data must never be baked into an image
**/.venv/
backend/data/
data/
**/.env
**/.env.*
```

This matters because `backend/data/youtube-watcher.db` (a real local dev database) and `backend/.venv` exist on the developer machine, and `COPY backend/ .` would otherwise copy them.

- [ ] **Step 7: Verify the image** (needs Docker and a `.env` copied from `.env.example`)

```bash
docker compose -f docker-compose-local.yml up --build -d
curl -s http://localhost:38000/api/health
docker compose -f docker-compose-local.yml run --rm --no-deps app python -c "import asyncio; from app.services.rss_parser import fetch_video_by_id; v = asyncio.run(fetch_video_by_id('dQw4w9WgXcQ')); print(v.title, v.channel_id, v.published_at)"
docker inspect --format '{{.State.Health.Status}}' $(docker compose -f docker-compose-local.yml ps -q app)
docker run --rm --entrypoint sh "$(docker compose -f docker-compose-local.yml images -q app | head -1)" -c 'ls -a /app; ls -a /app/data'
docker compose -f docker-compose-local.yml down
```

Expected:
- `/api/health` returns `{"status":"ok",...}`;
- the yt-dlp line prints a title, a `UC...` id and a date;
- the health status is `healthy` (wait about 35s first);
- the `ls` shows no `.venv` in `/app`, and `/app/data` holds only `.` and `..`.

**If the yt-dlp line fails or mentions a JavaScript runtime:** stop and report it, and don't add deno [B4]. If Docker isn't available, say so in the report; Task 24 repeats this check.

- [ ] **Step 8: Docs**
- `DEVELOPER_GUIDE.md` §4: add an "Updating dependencies" subsection — edit `requirements.txt`, rerun the Step 2 command, reinstall per Step 3, run tests, commit both files.
- `AGENTS.md` Development Commands: replace `cd backend && pytest` with the venv setup from Step 3 plus `.venv/bin/python -m pytest -m "not integration"`.

- [ ] **Step 9: Commit**

```bash
git add backend/requirements.txt backend/requirements.lock Dockerfile Dockerfile.dev docker-compose.dev.yml .dockerignore DEVELOPER_GUIDE.md AGENTS.md
git commit -m "build: hashed dependency lock, Python 3.13, Node 24, container healthcheck"
```

### Task 4: Run tests in CI and publish versioned images [B2, C10]

**Files:**
- Modify: `.github/workflows/docker-build.yml`

- [ ] **Step 1: Triggers and token scope.**
- Under `on.push.tags`, replace `- 'v*.*.*'` with `- 'v*'`.
- Add a top-level block after `env:` [S14]:

  ```yaml
  permissions:
    contents: read
  ```

  `build-and-push` keeps its own `permissions:` block (`contents: read`, `packages: write`).

- [ ] **Step 2: Add two jobs before `build-and-push`**, and add `needs: [backend-tests, frontend-check]` to `build-and-push`:

```yaml
  backend-tests:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v6
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: |
          pip install --require-hashes -r requirements.lock
          pip install -r requirements-dev.txt pip-audit
      - name: Run tests (offline)
        run: python -m pytest -m "not integration" -q
      - name: Audit dependencies
        run: pip-audit --disable-pip --require-hashes -r requirements.lock

  frontend-check:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-node@v5
        with:
          node-version: '24'
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - run: npm ci
      - run: npx tsc --noEmit
      - run: npm run lint
```

- [ ] **Step 3: Image tags.** In the `docker/metadata-action` `tags:` list, add `type=ref,event=tag` and keep the existing lines.

- [ ] **Step 4: Validate the YAML**

Run: `.venv/bin/python -c "import yaml; d = yaml.safe_load(open('../.github/workflows/docker-build.yml')); print(sorted(d['jobs']), d['jobs']['build-and-push']['needs'])"`
Expected: `['backend-tests', 'build-and-push', 'frontend-check'] ['backend-tests', 'frontend-check']`

- [ ] **Step 5: Commit**

```bash
git add .github/workflows/docker-build.yml
git commit -m "ci: gate image build on tests; build images for date-based release tags"
```

---

## Phase B — Subscriptions and saved videos stay independent

### Task 5: Unsubscribing discards inbox videos and keeps saved ones [C2]

**Files:**
- Create: `backend/tests/factories.py`
- Modify: `backend/app/routers/channels.py:194-215` (`delete_channel`)
- Modify: `backend/app/models/channel.py:22` (relationship)
- Test: `backend/tests/test_channel_delete.py`

**Interfaces:**
- Produces, in `tests/factories.py`, used by later tasks:
  - `make_channel(**overrides) -> Channel`. Defaults: `id=str(uuid4())`, `youtube_channel_id="UC-factory"`, `name="Factory Channel"`, with `rss_url`/`youtube_url` built from `get_rss_url`/`get_channel_url`.
  - `make_video(**overrides) -> Video`. Defaults: `id=str(uuid4())`, `youtube_video_id` = 11 chars from `uuid4().hex`, `title="Video"`, `video_url` built with `get_video_url`, `published_at=datetime(2026, 1, 1, tzinfo=UTC)`, `status="saved"`; `saved_at=datetime.now(UTC)` when the status is `saved`, otherwise `None`.
  - `async def reload(session, model, id)`. Calls `session.expire_all()`, then returns `await session.get(model, id)`.

- [ ] **Step 1: Write the factories**, then the failing tests in `test_channel_delete.py`:

```python
from datetime import datetime
from sqlalchemy import select, func
from app.models.channel import Channel
from app.models.video import Video
from tests.factories import make_channel, make_video, reload


async def test_unsubscribe_keeps_saved_and_discards_inbox(client, db_session):
    ch = make_channel()
    channel_id = ch.id
    common = dict(channel_id=channel_id, channel_youtube_id="UC-factory", channel_name="Factory Channel")
    saved = make_video(status="saved", **common)
    inbox = make_video(status="inbox", **common)
    old = make_video(status="discarded", discarded_at=datetime(2026, 1, 2), **common)
    saved_id, inbox_id, old_id = saved.id, inbox.id, old.id
    db_session.add(ch)
    db_session.add_all([saved, inbox, old])
    await db_session.commit()

    response = await client.delete(f"/api/channels/{channel_id}")
    assert response.status_code == 204

    assert await reload(db_session, Channel, channel_id) is None
    s = await reload(db_session, Video, saved_id)
    assert (s.status, s.channel_id, s.channel_youtube_id, s.channel_name) == ("saved", None, "UC-factory", "Factory Channel")
    assert s.saved_at is not None
    i = await reload(db_session, Video, inbox_id)
    assert (i.status, i.channel_id, i.saved_at) == ("discarded", None, None)
    assert i.discarded_at is not None
    o = await reload(db_session, Video, old_id)
    assert o.discarded_at == datetime(2026, 1, 2)
    remaining = await db_session.execute(select(func.count()).select_from(Video).where(Video.channel_id == channel_id))
    assert remaining.scalar_one() == 0


def test_channel_relationship_never_cascades_deletes():
    cascade = Channel.videos.property.cascade
    assert not cascade.delete and not cascade.delete_orphan
```

- [ ] **Step 2: Run them to confirm they fail**

Run: `.venv/bin/python -m pytest tests/test_channel_delete.py -q`
Expected: the first test fails because the saved video's `channel_id` is still set; the second fails because `CascadeOptions(...).delete` is True. (This exact test pair was checked in a scratch copy: it fails before the fix and passes after.)

- [ ] **Step 3: Implement `delete_channel`.** After the existing 404 check, run three statements and then commit:
1. `update(Video)` where `channel_id == channel_id` and `status == 'inbox'` → `status='discarded'`, `discarded_at=now`, `saved_at=None`.
2. `update(Video)` where `channel_id == channel_id` → `channel_id=None`.
3. The existing `delete(Channel)`.

Also:
- replace the docstring with the Global Constraints rule, plus one sentence saying why foreign keys are not relied on;
- in `models/channel.py`, change the relationship to `relationship("Video", back_populates="channel")` with a comment: `# No delete cascade: unsubscribing must never delete saved videos.`

- [ ] **Step 4: Run the tests**

Run `tests/test_channel_delete.py`, then the offline suite. Expected: all pass.

- [ ] **Step 5: Commit**

```bash
git add backend/tests/factories.py backend/tests/test_channel_delete.py backend/app/routers/channels.py backend/app/models/channel.py
git commit -m "fix: unsubscribing keeps saved videos and moves inbox videos to Recently Deleted"
```

### Task 6: Frontend copy and cache refresh for unsubscribing [C2]

**Files:**
- Modify: `frontend/src/hooks/useChannels.ts:30-32`
- Modify: `frontend/src/components/channel/ChannelCard.tsx:20`
- Modify: `frontend/src/components/channel/ChannelListView.tsx:111`

- [ ] **Step 1:** In `useDeleteChannel().onSuccess`, also call `queryClient.invalidateQueries({ queryKey: ['videos'] })`.

- [ ] **Step 2:** In both components, replace the `window.confirm` text with exactly:

```ts
`Unsubscribe from "${channel.name}"?\n\nIts inbox videos will move to Recently Deleted. Saved videos stay in your library.`
```

- [ ] **Step 3: Verify**

Run: `cd frontend && npx tsc --noEmit && npm run lint`
Expected: tsc exits 0; lint reports 0 errors (the 12 existing warnings are fine).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/hooks/useChannels.ts frontend/src/components/channel/ChannelCard.tsx frontend/src/components/channel/ChannelListView.tsx
git commit -m "feat(frontend): explain unsubscribe effects and refresh video lists after it"
```

### Task 7: Safe database backups and an honest backup status [C5, C6]

**Files:**
- Modify: `backend/app/services/backup_service.py` (remove `BACKUP_DIR`, `DATABASE_PATH`, `/app`)
- Modify: `backend/app/routers/backup.py:125-157` (`run_manual_backup`)
- Test: `backend/tests/test_backup_service.py`

**Interfaces:**
- Produces, in `backup_service`:
  - `get_database_path() -> Path`, which returns `Path(make_url(app_settings.database_url).database)` (`make_url` comes from `sqlalchemy.engine`);
  - `get_backup_dir() -> Path`, which returns `get_database_path().parent / "backups"`.
- Every former `BACKUP_DIR` use calls `get_backup_dir()`. Check with `grep -rn BACKUP_DIR backend/app`.

- [ ] **Step 1: Write the failing tests.** Fixture `file_db(tmp_path, monkeypatch)`:
- creates `tmp_path / "data" / "app.db"` with a sync `create_engine(f"sqlite:///{path}")` and `Base.metadata.create_all`;
- inserts one channel through a sync `Session` (`make_channel()`);
- monkeypatches `app.services.backup_service.get_database_path` to return that path;
- returns it.

The tests:
- `test_database_path_from_url(monkeypatch)`: set `app.config.settings.database_url` to `"sqlite+aiosqlite:///./data/x.db"` and expect `Path("data/x.db")`; set it to `"sqlite+aiosqlite:////srv/x.db"` and expect `Path("/srv/x.db")`.
- `test_backup_dir_next_to_database(file_db)`: `get_backup_dir() == file_db.parent / "backups"`.
- `test_database_backup_is_valid_sqlite(file_db)`:
  - `ok, name, err = await BackupService.create_database_backup()`; assert `ok and err is None`;
  - gunzip `get_backup_dir() / name` into `tmp_path / "restored.db"`;
  - `sqlite3.connect(...).execute("select count(*) from channels").fetchone() == (1,)`;
  - `not any(p.name.startswith(".tmp_") for p in get_backup_dir().iterdir())`.
- `test_manual_backup_failure_is_recorded(client, db_session, mocker)`:
  - add `Setting(id="1")` and commit;
  - `mocker.patch("app.routers.backup.BackupService.create_backup", AsyncMock(return_value=(False, [], "boom")))`;
  - `POST /api/backup/run` with `{"format": "json"}`;
  - then `GET /api/backup/status` returns `last_backup_status == "failed"` and `last_backup_error == "boom"`.

- [ ] **Step 2: Run them to confirm they fail** (ImportError for `get_database_path`; status `None` for the API test).

- [ ] **Step 3: Implement**
- Add `get_database_path` and `get_backup_dir`.
- `_create_json_backup_sync` reads from `get_database_path()`.
- `_create_database_backup_sync`:
  - `src = sqlite3.connect(db_path)`;
  - `tmp = get_backup_dir() / f".tmp_{filename[:-3]}"`;
  - `dst = sqlite3.connect(tmp)`;
  - `src.backup(dst)`; close both;
  - gzip `tmp` into the final file; unlink `tmp` in a `finally`.
  - Return the same `(success, filename, error)` tuples as today, including "Database file not found: ..." when the DB is missing.
- `run_manual_backup`:
  - always write `last_backup_at`, `last_backup_status` (`'success' if success else 'failed'`) and `last_backup_error` (`error`);
  - run retention cleanup only on success.

- [ ] **Step 4: Run the tests** — `tests/test_backup_service.py`, then the offline suite. Expected: pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/backup_service.py backend/app/routers/backup.py backend/tests/test_backup_service.py
git commit -m "fix(backup): use SQLite backup API, derive paths from DATABASE_URL, record failures"
```

### Task 8: Exports and the JSON backup keep channel info for unsubscribed videos [C4]

**Files:**
- Modify: `backend/app/schemas/mappers.py` (add a function)
- Modify: `backend/app/routers/import_export.py` (`export_saved_videos`, `export_all`)
- Modify: `backend/app/services/backup_service.py` (the saved-videos SQL in `_create_json_backup_sync`)
- Test: `backend/tests/test_export_channel_info.py`

**Interfaces:**
- Consumes: `get_database_path` (Task 7) and `tests/factories` (Task 5).
- Produces: `map_video_to_export(video: Video) -> VideoExport`:
  - `channel_youtube_id = video.channel_youtube_id or (video.channel.youtube_channel_id if video.channel else None)`;
  - `channel_name = video.channel_name or (video.channel.name if video.channel else None)`;
  - `channel_url = video.channel.youtube_url if video.channel else (get_channel_url(cyid) if cyid else None)`.

- [ ] **Step 1: Write the failing tests.** The setup adds a saved video with `channel_id=None`, `channel_youtube_id="UC-gone"`, `channel_name="Gone Channel"` and commits. Expected entry for that video:

```python
EXPECTED = {"channel_youtube_id": "UC-gone", "channel_name": "Gone Channel",
            "channel_url": "https://www.youtube.com/channel/UC-gone"}
```

- `test_export_all_keeps_unsubscribed_channel_info`: in `GET /api/import-export/export/all`, the entry in `saved_videos` has `EXPECTED` as a subset.
- `test_export_saved_videos_keeps_unsubscribed_channel_info`: the same for `/export/saved-videos`.
- `test_json_backup_keeps_unsubscribed_channel_info`: reuse the `file_db` fixture idea from Task 7, but insert the video through the sync session; run `await BackupService.create_json_backup(None)`; `json.load(gzip.open(...))["saved_videos"][0]` has `EXPECTED` as a subset.

- [ ] **Step 2: Run them to confirm they fail** (`channel_youtube_id` is `None`).

- [ ] **Step 3: Implement**
- Both export endpoints build entries with `map_video_to_export`.
- In the backup SQL, select `v.channel_youtube_id` and `COALESCE(v.channel_name, c.name) AS channel_name`, with `c.youtube_url AS channel_url` from `LEFT JOIN channels c ON c.id = v.channel_id`. In Python, fill a missing `channel_url` with `get_channel_url(channel_youtube_id)` when that id is present.

- [ ] **Step 4: Run the tests** (pass) and the offline suite.

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/mappers.py backend/app/routers/import_export.py backend/app/services/backup_service.py backend/tests/test_export_channel_info.py
git commit -m "fix: exports and backups keep channel info for videos from unsubscribed channels"
```

### Task 9: One import pipeline for URL lists and playlists [C3, P3, S2]

**Files:**
- Create: `backend/app/services/video_import_service.py`
- Modify: `backend/app/routers/import_export.py` (`import_video_urls`, `import_playlist`; delete both local `FetchResult` classes)
- Test: `backend/tests/test_video_import_service.py`

**Interfaces:**
- Produces:
  - `IMPORT_CONCURRENCY = 4`
  - `async def import_videos_by_id(db: AsyncSession, youtube_video_ids: list[str], timeout: float) -> VideoImportResult`
- The service imports `from .rss_parser import fetch_video_by_id`; tests patch `app.services.video_import_service.fetch_video_by_id`.
- The router keeps `fetch_playlist_video_ids` imported; tests patch `app.routers.import_export.fetch_playlist_video_ids`.

Behavior of `import_videos_by_id`, in order:
1. `total = len(youtube_video_ids)`. Repeats of an id already seen in this call count as `skipped`.
2. Run one `select(Video).where(Video.youtube_video_id.in_(unique_ids))`. For existing rows: if the status isn't `saved`, set `status='saved'`, `saved_at=now`, `discarded_at=None` and count `imported`; otherwise count `skipped`. Never fetch these from the network.
3. Fetch the remaining ids with `fetch_video_by_id(id, timeout=timeout)` under `asyncio.Semaphore(IMPORT_CONCURRENCY)` via `asyncio.gather`. A failure appends `f"Could not fetch video {id}"` to `errors`.
4. Run one `select(Channel.youtube_channel_id, Channel.id).where(Channel.youtube_channel_id.in_(fetched channel ids))` to find subscriptions.
5. Add one `Video` per fetched video:
   - `channel_id` = the subscription id or `None`, plus `channel_youtube_id` and `channel_name` from the fetched info;
   - `channel_thumbnail_url=None`, `description or ""`, `status='saved'`, `saved_at=now`, `is_short` from the fetched info.
   Never create a `Channel` and never call `fetch_channel_info`.
6. Commit once and return the result.

Router changes:
- `import_video_urls`: strip each URL and skip empty ones (they count only toward `total`). Invalid URLs go into `errors` as `f"Invalid YouTube URL: {url}"`. Call the service with the parsed ids in order, then return `total=len(request.urls)`, the service's `imported`/`skipped`, and `errors = url_errors + service errors`.
- `import_playlist`:
  - `playlist_id = extract_playlist_id(request.url)`; on `ValueError`, return `VideoImportResult(total=0, imported=0, skipped=0, errors=[str(e)])` without calling yt-dlp;
  - otherwise call `fetch_playlist_video_ids(f"https://www.youtube.com/playlist?list={playlist_id}", timeout=timeout)` (keep the existing `ValueError` handling), then the service.

- [ ] **Step 1: Write the failing tests.** Add a helper, `info(video_id, channel_id="UC-unsub", channel_name="Unsub Channel") -> VideoInfo`, with title `f"T {video_id}"`, `video_url=get_video_url(video_id)` and `published_at=datetime(2026, 1, 1, tzinfo=UTC)`. Patch `fetch_video_by_id` with `AsyncMock(side_effect=lambda vid, timeout: info(vid))` unless a test says otherwise. Use 11-character ids such as `"a" * 11`.
- `test_url_import_does_not_subscribe`: `POST /api/import-export/import/video-urls` with `{"urls": [f"https://www.youtube.com/watch?v={'a'*11}"]}`.
  - Response `imported == 1`.
  - The channel count is 0.
  - The stored video has `channel_id is None`, `channel_youtube_id == "UC-unsub"`, `channel_name == "Unsub Channel"` and `status == "saved"`.
- `test_url_import_links_existing_subscription(sample_channel)`: capture `sample_id = sample_channel.id` first; mock with `channel_id="UC-test123"`; the stored video has `channel_id == sample_id`.
- `test_url_import_resaves_existing_without_fetch`:
  - set up an existing video with `youtube_video_id="b"*11` and `status="discarded"`;
  - import its URL;
  - assert `fetch_video_by_id` was not awaited, `imported == 1`, the row is `saved`, and `discarded_at is None`.
- `test_url_import_duplicates_invalid_and_blank`:
  - URLs: the `a` URL twice, `"https://example.com/x"`, and `""`;
  - result: `total == 4`, `imported == 1`, `skipped == 1`, `errors == ["Invalid YouTube URL: https://example.com/x"]`, and the fetch was awaited once.
- `test_url_import_reports_fetch_failure`: the mock raises `ValueError("gone")`; `errors == [f"Could not fetch video {'c'*11}"]`.
- `test_playlist_rejects_non_youtube_url`: patch `fetch_playlist_video_ids` with `AsyncMock()`; post `{"url": "http://169.254.169.254/latest"}`; the status is 200, `errors[0]` starts with `"Unrecognized YouTube playlist URL format"`, and the mock was not awaited.
- `test_playlist_uses_canonical_url`: post `{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ&list=PL123abc"}` with the playlist mock returning `["d"*11]`; the first positional argument of the mock's await is `"https://www.youtube.com/playlist?list=PL123abc"`, and `imported == 1`.

- [ ] **Step 2: Run them to confirm they fail** (a channel gets created, the fetch is called for an existing video, and the playlist URL is passed through raw).

- [ ] **Step 3: Implement** the service and router changes above. Remove imports that are now unused from the router.

- [ ] **Step 4: Run the tests** — the new file, the offline suite, and `tests/test_import_playlist.py` with network if available.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/video_import_service.py backend/app/routers/import_export.py backend/tests/test_video_import_service.py
git commit -m "fix(import): never subscribe on video import, check DB before fetching, validate playlist URLs"
```

### Task 10: The JSON saved-video import never subscribes or hits the network [C3]

**Files:**
- Modify: `backend/app/routers/import_export.py` (`import_videos`)
- Test: `backend/tests/test_import_saved_videos.py`

Behavior:
- `total = len(request.videos)`; duplicate `youtube_video_id`s within the request count as `skipped`.
- One `IN` query finds existing videos and one finds subscriptions.
- An existing video that isn't saved becomes `saved`, with `saved_at = item.saved_at or now` and `discarded_at=None`, and counts as `imported`. An existing saved video counts as `skipped`.
- A new video is created from the export data, exactly as today, except:
  - `channel_id` = the subscription id or `None`;
  - no `Channel` is created and `fetch_channel_info` is never called.
- Commit once.

- [ ] **Step 1: Write the failing tests.** In each, patch `app.routers.import_export.fetch_channel_info` with `AsyncMock(side_effect=AssertionError("network"))`. A payload item looks like `{"youtube_video_id": "e"*11, "title": "E", "video_url": get_video_url("e"*11), "channel_youtube_id": "UC-unsub", "channel_name": "Unsub Channel", "channel_url": None, "saved_at": None, "published_at": "2026-01-01T00:00:00Z"}`.
- `test_json_import_does_not_subscribe_or_fetch`: `imported == 1`, the channel count is 0, and the video has `channel_name == "Unsub Channel"`.
- `test_json_import_links_existing_subscription(sample_channel)`: `channel_youtube_id="UC-test123"`, so the video's `channel_id == sample_id`.
- `test_json_import_resaves_discarded`: an existing discarded `"e"*11` becomes `saved` with `discarded_at is None`, and `imported == 1`.
- `test_json_import_duplicate_items`: the same item twice gives `imported == 1`, `skipped == 1` and `errors == []`.

- [ ] **Step 2: Run them to confirm they fail.** Expected: `AssertionError: network` (the code tries to create the channel).

- [ ] **Step 3: Implement** the behavior above.

- [ ] **Step 4: Run the tests** (pass) and the offline suite.

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/import_export.py backend/tests/test_import_saved_videos.py
git commit -m "fix(import): JSON saved-video import links only existing subscriptions"
```

---

## Phase C — Performance

### Task 11: Keep yt-dlp off the event loop [P1, P2]

**Files:**
- Modify: `backend/app/services/rss_parser.py` (`fetch_video_by_id`, `fetch_playlist_video_ids`)
- Test: `backend/tests/test_rss_parser_offline.py`

**Interfaces:**
- Produces: `_extract_info(url: str, opts: dict) -> dict`, the synchronous `YoutubeDL(opts).extract_info(url, download=False)` call. Both async functions call `await asyncio.to_thread(_extract_info, url, opts)`.
- Both functions add `"socket_timeout": timeout` and `"extractor_retries": 3` to their opts. Remove the `@retry` decorators from **these two functions only**.

- [ ] **Step 1: Write the failing tests.** Use a fake info dict: `{"title": "T", "uploader": "U", "channel_id": "UC-x", "upload_date": "20260101", "webpage_url": "https://www.youtube.com/watch?v=" + "f"*11}`.
- `test_fetch_video_by_id_does_not_block_loop(monkeypatch)`:
  - patch `rss_parser._extract_info` with a function that calls `time.sleep(0.3)` and returns the fake;
  - run `asyncio.gather(fetch_video_by_id("f"*11), ticker())`, where `ticker` counts `await asyncio.sleep(0.01)` iterations for 0.25s;
  - assert the tick count is at least 10.
- `test_fetch_video_by_id_passes_socket_timeout`: capture `opts`; `await fetch_video_by_id("f"*11, timeout=7.0)`; assert `opts["socket_timeout"] == 7.0` and `opts["extractor_retries"] == 3`.
- `test_download_error_becomes_value_error_once`:
  - the patch raises `yt_dlp.utils.DownloadError("x")` and counts calls;
  - `pytest.raises(ValueError)`;
  - `calls == 1`.

- [ ] **Step 2: Run them to confirm they fail** (`AttributeError: _extract_info`).

- [ ] **Step 3: Implement** as in Interfaces.

- [ ] **Step 4: Run the tests** (pass) and the offline suite.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/rss_parser.py backend/tests/test_rss_parser_offline.py
git commit -m "perf: run yt-dlp in a worker thread and honor the HTTP timeout"
```

### Task 12: Faster, serialized feed refresh with honest status [P4, C7, C6]

**Files:**
- Modify: `backend/app/services/channels_service.py`
- Modify: `backend/app/routers/channels.py` (`create_channel` shorts block and existence loop; `refresh_channel`)
- Modify: `backend/app/services/feed_refresh_scheduler.py` (`run_scheduled_refresh`)
- Test: `backend/tests/test_refresh.py`

**Interfaces:**
- Produces, in `channels_service`:
  - `refresh_lock = asyncio.Lock()`;
  - `async def detect_and_store_shorts(db: AsyncSession, youtube_video_ids: list[str]) -> None`. A no-op for an empty list or when `get_auto_detect_shorts` is False. Otherwise it runs one `detect_shorts_batch_http(ids, timeout=await get_http_timeout(db))` and the per-id UPDATEs currently inline; exceptions are logged, not raised.
  - `async def process_new_videos(db, channel, videos_info, *, detect_shorts: bool = True) -> list[str]`, which now returns the new youtube ids instead of a count. Keep today's loop semantics exactly:
    - stop at `channel.last_video_id`;
    - skip existing videos;
    - `last_video_id` becomes the first new video;
    - always update `last_checked`.
    Replace the per-entry SELECT with one `select(Video.youtube_video_id).where(Video.youtube_video_id.in_(feed_ids))`, and also skip ids repeated within the feed. Calls `detect_and_store_shorts` when `detect_shorts`.
  - `refresh_all_channels(db) -> RefreshSummary` (same signature):
    - the whole body runs inside `async with refresh_lock:`;
    - each channel is processed with `detect_shorts=False`, collecting ids;
    - one `detect_and_store_shorts(db, all_ids)` runs before the commit;
    - `new_videos_found` sums the list lengths.
- Produces, in `feed_refresh_scheduler`: `summarize_refresh_outcome(summary: RefreshSummary) -> tuple[str, str | None]`:
  - no errors → `("success", None)`;
  - errors with `channels_refreshed > 0` → `"success"`;
  - errors with `channels_refreshed == 0` → `"failed"`;
  - the message is `f"{len(errors)} channel(s) failed. First error: {errors[0]}"[:500]`.

  `run_scheduled_refresh` writes these values instead of the hard-coded `'success'`/`None`.
- Router changes:
  - `refresh_channel` wraps its fetch, process and commit in `async with refresh_lock:`;
  - `create_channel` replaces its per-video existence SELECT with one `IN` query, and its inline shorts block with `await detect_and_store_shorts(db, new_video_ids)`.

- [ ] **Step 1: Write the failing tests.** Patch `app.services.channels_service.fetch_videos` and `app.services.channels_service.detect_shorts_batch_http` (`AsyncMock(return_value={})`). Build `VideoInfo` objects like Task 9's helper, with ids `"v" + str(n).zfill(10)` (11 characters).
- `test_process_new_videos_stops_at_last_known_and_skips_existing`:
  - the channel has `last_video_id = vid(3)`; the DB already has `vid(2)`; the feed is `[vid(1), vid(2), vid(3), vid(4)]`;
  - `process_new_videos(..., detect_shorts=False)` returns `[vid(1)]`;
  - the reloaded channel has `last_video_id == vid(1)`;
  - the shorts mock was not awaited.
- `test_refresh_all_detects_shorts_once_for_all_channels`:
  - two channels each get one new video;
  - the shorts mock is awaited once, with `set(args[0]) == {both ids}`;
  - the response has `new_videos_found == 2`.
- `test_refresh_all_holds_lock`: with **one channel in the DB** (otherwise the fake is never called), the fake `fetch_videos` asserts `channels_service.refresh_lock.locked()` and returns `[]`. `POST /api/channels/refresh-all` returns 200, and the response has `channels_refreshed == 1`.
- `test_refresh_channel_holds_lock`: the same, with one channel, patching `app.routers.channels.fetch_videos` and calling `POST /api/channels/{id}/refresh`.
- `test_summarize_refresh_outcome` (parametrized):
  - `(2, [])` → `("success", None)`;
  - `(2, ["X"])` → `("success", "1 channel(s) failed. First error: X")`;
  - `(0, ["X", "Y"])` → `("failed", "2 channel(s) failed. First error: X")`.

  Each case builds `RefreshSummary(channels_refreshed=n, new_videos_found=0, errors=errs)`.

- [ ] **Step 2: Run them to confirm they fail** (missing names; `process_new_videos` returns an int).

- [ ] **Step 3: Implement** as in Interfaces.

- [ ] **Step 4: Run the tests** (pass), the offline suite, and the full suite if you have network (`TestRefreshChannel` and `TestRefreshAllChannels` exercise the real path).

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/channels_service.py backend/app/routers/channels.py backend/app/services/feed_refresh_scheduler.py backend/tests/test_refresh.py
git commit -m "perf: batch refresh queries and shorts detection, serialize refreshes, report partial failures"
```

### Task 13: Reuse one HTTP client per batch [P5]

**Files:**
- Modify: `backend/app/services/youtube_utils.py` (add a factory and use it in `_fetch_channel_id_from_page`)
- Modify: `backend/app/services/rss_parser.py` (`fetch_channel_info`, `fetch_videos`)
- Modify: `backend/app/services/shorts_detector.py` (`detect_short_http`, `detect_shorts_batch_http`)
- Modify: `backend/app/services/channels_service.py` (`fetch_channel_videos`, `refresh_all_channels`)
- Test: `backend/tests/test_http_client_reuse.py`

**Interfaces:**
- Produces: `make_youtube_client(timeout: float, follow_redirects: bool = True) -> httpx.AsyncClient`. It applies `HTTP_HEADERS` and `YOUTUBE_COOKIES`. Every `httpx.AsyncClient(...)` construction in these services is replaced by it.
- Changed signatures, each with a new trailing `client: httpx.AsyncClient | None = None`:
  - `fetch_videos(rss_url, limit=15, timeout=10.0, client=None)`
  - `detect_short_http(video_id, timeout=5.0, client=None)`
  - `fetch_channel_videos(channel, timeout, client=None)`

  When `client` is None the function opens and closes its own; it never closes a client that was passed in.
- `detect_shorts_batch_http` opens one `make_youtube_client(timeout, follow_redirects=False)` and passes it to every check. `refresh_all_channels` opens one `make_youtube_client(timeout)` around its gather and passes it to `fetch_channel_videos`.

- [ ] **Step 1: Write the failing tests**, using the existing `httpx.AsyncClient` patching style from `tests/test_youtube_utils.py`:
- `test_shorts_batch_uses_one_client(mocker)`:
  - `mocker.patch("httpx.AsyncClient")` returns a mock client whose `get` returns `MagicMock(status_code=303)` and that supports `async with`;
  - `await detect_shorts_batch_http(["a"*11, "b"*11, "c"*11])` returns three `False` values;
  - the patched constructor was called exactly once.
- `test_fetch_videos_uses_passed_client(mocker)`:
  - `mocker.patch("httpx.AsyncClient", side_effect=AssertionError("new client"))`;
  - pass a mock client whose `get` returns a response with a no-op `raise_for_status` and `.content` set to this feed:

    ```python
    FEED = b"""<?xml version="1.0" encoding="UTF-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom" xmlns:yt="http://www.youtube.com/xml/schemas/2015">
      <title>G Channel</title><yt:channelId>UC-g</yt:channelId>
      <entry><yt:videoId>ggggggggggg</yt:videoId><title>G</title>
        <published>2026-01-01T00:00:00+00:00</published></entry>
    </feed>"""
    ```

  - the result has one video with `video_id == "g"*11`.

- [ ] **Step 2: Run them to confirm they fail** (the constructor is called 3 times; `TypeError: unexpected keyword 'client'`).

- [ ] **Step 3: Implement** as in Interfaces.

- [ ] **Step 4: Run the tests** (pass), the offline suite (`test_youtube_utils` mocks must still pass), and the full suite if you have network.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/youtube_utils.py backend/app/services/rss_parser.py backend/app/services/shorts_detector.py backend/app/services/channels_service.py backend/tests/test_http_client_reuse.py
git commit -m "perf: reuse one HTTP client per refresh and shorts batch"
```

### Task 14: Bulk status changes in one statement; request size caps [P6, P9]

**Files:**
- Modify: `backend/app/routers/videos.py` (`bulk_save_videos`, `bulk_discard_videos`, `list_inbox_videos` limit, `BatchDetectRequest`)
- Modify: `backend/app/schemas/video.py` (`BulkVideoAction`)
- Modify: `backend/app/schemas/import_export.py` (request lists)
- Test: `backend/tests/test_bulk_and_limits.py`

**Interfaces:**
- Produces: `async def _bulk_set_status(db: AsyncSession, video_ids: list[str], status: str) -> list[Video]` in `videos.py`:
  - one `update(Video).where(Video.id.in_(ids)).values(...).execution_options(synchronize_session=False)`;
  - `saved` sets `saved_at=now, discarded_at=None`; `discarded` sets `discarded_at=now, saved_at=None`;
  - commit, then one `select(Video).options(selectinload(Video.channel)).where(Video.id.in_(ids))`.

  Both bulk endpoints return `[map_video_to_response(v) for v in videos]`.
- Caps:
  - `BulkVideoAction.video_ids: List[str] = Field(max_length=10000)`
  - `list_inbox_videos` `limit: Query(10000, ge=1, le=10000)`
  - `BatchDetectRequest.video_ids: Optional[List[str]] = Field(default=None, max_length=10000)`
  - `ImportChannelsRequest.channels` max_length 5000; `ImportVideosRequest.videos` 100000; `ImportUrlsRequest.urls` 1000.

- [ ] **Step 1: Write the failing tests:**
- `test_bulk_save_updates_all(client, db_session)`:
  - two inbox videos (factories, with `channel_name="C"`); capture ids;
  - `POST /api/videos/bulk-save` returns 200, the response's set of ids equals both, and every item has `status == "saved"` and `channel_name == "C"`.
- `test_bulk_discard_updates_all`: the mirror image, with `discarded_at` not None.
- `test_bulk_rejects_more_than_10000_ids`: 10001 copies of a valid UUID string give 422.
- `test_bulk_accepts_10000_ids`: 10000 give 200 and `[]`.
- `test_inbox_limit_capped`: `GET /api/videos/inbox?limit=10001` gives 422, and `limit=10000` gives 200.
- `test_import_urls_capped`: 1001 URLs give 422.

- [ ] **Step 2: Run them to confirm they fail** (422 cases return 200).

- [ ] **Step 3: Implement** as in Interfaces.

- [ ] **Step 4: Run the tests** (pass) and the offline suite.

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/videos.py backend/app/schemas/video.py backend/app/schemas/import_export.py backend/tests/test_bulk_and_limits.py
git commit -m "perf: single-statement bulk save/discard; cap request sizes"
```

### Task 15: Composite indexes for the list queries [P7]

**Files:**
- Create: `backend/alembic/versions/20261020_1200_c3d4e5f6a7b8_add_video_list_indexes.py`
- Modify: `backend/app/models/video.py` (add `__table_args__`)
- Test: `backend/tests/test_indexes.py`

**Interfaces:**
- The migration has `revision = 'c3d4e5f6a7b8'` and `down_revision = 'b2c3d4e5f6g7'` (the current head; confirm with `.venv/bin/alembic heads`).
- Index names and columns, identical in the migration and the model:
  - `ix_videos_status_published_at` (`status`, `published_at`)
  - `ix_videos_status_saved_at` (`status`, `saved_at`)
  - `ix_videos_status_is_short_published_at` (`status`, `is_short`, `published_at`)
- `upgrade()` calls `op.create_index(name, 'videos', cols, if_not_exists=True)` for each; `downgrade()` calls `op.drop_index(name, table_name='videos', if_exists=True)`.

- [ ] **Step 1: Write the failing test** `test_video_list_indexes_exist(db_session)`. Query `select name from sqlite_master where type='index' and tbl_name='videos'` (via `text()`) and assert the three names are a subset of the result.

- [ ] **Step 2: Run it to confirm it fails.**

- [ ] **Step 3: Add `__table_args__`** with three `sqlalchemy.Index` objects, and write the migration.

- [ ] **Step 4: Verify** the test passes, and the migration runs both directions on a scratch database:

```bash
SCRATCH=$(mktemp -d) && cp -R alembic alembic.ini app "$SCRATCH"/ && mkdir "$SCRATCH/data"
(cd "$SCRATCH" && "$OLDPWD/.venv/bin/alembic" upgrade head && "$OLDPWD/.venv/bin/alembic" downgrade -1 && "$OLDPWD/.venv/bin/alembic" upgrade head)
sqlite3 "$SCRATCH/data/youtube-watcher.db" "EXPLAIN QUERY PLAN SELECT * FROM videos WHERE status='saved' AND is_short=0 ORDER BY published_at LIMIT 50"
```

Expected: no errors, and the plan says `USING INDEX ix_videos_status_is_short_published_at`.

- [ ] **Step 5: Commit**

```bash
git add backend/alembic/versions/20261020_1200_c3d4e5f6a7b8_add_video_list_indexes.py backend/app/models/video.py backend/tests/test_indexes.py
git commit -m "perf: composite indexes for inbox, saved and QuickPlay queries"
```

---

## Phase D — Security hardening

### Task 16: Versioned password hashes at 600k iterations [S3]

**Files:**
- Modify: `backend/app/auth.py` (`hash_password`, `verify_password`, constants)
- Modify: `scripts/generate-password-hash.sh`, `.env.example` (hash comment), `README.md` (auth section, if it describes the hash length)
- Test: `backend/tests/test_auth.py`

**Interfaces:**
- Constants: `PBKDF2_ITERATIONS = 600_000`, `LEGACY_PBKDF2_ITERATIONS = 100_000`, `HASH_SCHEME = "pbkdf2_sha256"`.
- `hash_password(password: str) -> str` returns `f"{HASH_SCHEME}.{iterations}.{b64(salt)}.{b64(digest)}"`. It uses unpadded urlsafe base64 and a 16-byte salt, so the string matches `[A-Za-z0-9_.-]+`.
- `verify_password(plain: str, hashed: str) -> bool`:
  - a string starting with `"pbkdf2_sha256."` must split into exactly 4 parts, with iterations an int in `[100_000, 10_000_000]`;
  - anything else goes through today's legacy 48-byte path at `LEGACY_PBKDF2_ITERATIONS`;
  - malformed input returns False; comparisons use `secrets.compare_digest`.
- The script prints the new format, generated with the same algorithm at 600000 iterations.

- [ ] **Step 1: Write the failing tests:**
- `test_hash_roundtrip`: `verify_password("pw", hash_password("pw"))`, and `not verify_password("nope", ...)`.
- `test_hash_format`: `h.split(".")[:2] == ["pbkdf2_sha256", "600000"]` and `re.fullmatch(r"[A-Za-z0-9_.\-]+", h)`.
- `test_legacy_hash_still_verifies`: build a legacy hash in the test exactly as the old script did (16-byte salt + PBKDF2-SHA256 at 100000, urlsafe b64 with `=` stripped); verifying "pw" passes.
- `test_malformed_hashes_rejected`: `""`, `"pbkdf2_sha256.abc.x.y"`, `"pbkdf2_sha256.50.x.y"` and `"!!!"` all return False.
- `test_script_output_verifies`:
  - `subprocess.run(["bash", "../scripts/generate-password-hash.sh", "s3cret"], capture_output=True, text=True, check=True)`;
  - take the value after the last `AUTH_PASSWORD_HASH=`;
  - `verify_password("s3cret", value)`.

- [ ] **Step 2: Run them to confirm they fail** (format / script assertions).

- [ ] **Step 3: Implement** the auth changes and update the script (output text: "(~90 characters)").

- [ ] **Step 4: Run the tests** (pass) and the offline suite.

- [ ] **Step 5: Commit**

```bash
git add backend/app/auth.py scripts/generate-password-hash.sh .env.example README.md backend/tests/test_auth.py
git commit -m "feat(auth): versioned PBKDF2 hashes at 600k iterations with legacy support"
```

### Task 17: Login rate limit, off-loop hashing, constant-time username [S3, S9, S10]

**Files:**
- Modify: `backend/app/auth.py` (`authenticate_user`; add the limiter)
- Modify: `backend/app/routers/auth.py` (`login`)
- Modify: `README.md` (auth section: one sentence on the lockout and the reverse-proxy caveat)
- Test: `backend/tests/test_login.py`

**Interfaces:**
- Produces: `class LoginRateLimiter` with:
  - `__init__(self, max_failures: int = 10, window_seconds: float = 900.0, clock: Callable[[], float] = time.monotonic)`;
  - `retry_after(key: str) -> float` (0.0 when not blocked);
  - `record_failure(key: str) -> None`, `reset(key: str) -> None` and `clear() -> None`.

  A key is blocked once it has `max_failures` failures newer than `window_seconds`. Module instance: `login_limiter = LoginRateLimiter()`.
- `authenticate_user(username, password) -> bool`. If auth is disabled it returns True. Otherwise it **always** computes both `secrets.compare_digest(username.encode(), settings.auth_username.encode())` and `verify_password(...)`, and returns their logical AND.
- `login(request: LoginRequest, http_request: Request)`:
  - `key = http_request.client.host if http_request.client else "unknown"`;
  - if `retry_after(key) > 0`, raise HTTP 429 with detail `"Too many failed login attempts. Try again later."` and header `Retry-After: str(math.ceil(seconds))`;
  - else `ok = await asyncio.to_thread(authenticate_user, ...)`;
  - a failure records it and returns 401; a success resets the key and returns a token.
- `LoginRequest` (in `routers/auth.py`): `username: str = Field(max_length=256)`, `password: str = Field(max_length=1024)` [S10].
- `require_auth` compares the API key as bytes: `secrets.compare_digest(x_api_key.encode(), settings.api_key.encode())` [S9].

- [ ] **Step 1: Write the failing tests.** An autouse fixture calls `login_limiter.clear()`. An `auth_on(monkeypatch)` fixture:
- first monkeypatches `app.auth.PBKDF2_ITERATIONS` to `100_000`, so the ~30 hashes in these tests stay fast;
- then sets `app.config.settings` fields: `auth_enabled=True`, `auth_username="admin"`, `auth_password_hash=hash_password("pw")`.
- `test_limiter_blocks_after_threshold_and_expires`:
  - clock `t = [0.0]`; `LoginRateLimiter(max_failures=3, window_seconds=60, clock=lambda: t[0])`;
  - 3 failures → `retry_after("ip") > 0`;
  - `t[0] = 61` → `retry_after("ip") == 0`.
- `test_reset_clears_failures`.
- `test_login_locks_out_after_10_failures(client, auth_on)`:
  - 10 × wrong password → 401;
  - the 11th, with the **correct** password, → 429 with a `Retry-After` header.
- `test_successful_login_resets(client, auth_on)`: 9 wrong, 1 right (200), then 9 wrong again; all are 401, none 429.
- `test_wrong_username_rejected(client, auth_on)` → 401.
- `test_oversized_password_rejected(client, auth_on)`: a 1025-character password → 422.
- `test_non_ascii_api_key_is_401(client, monkeypatch)`:
  - set `auth_enabled=True` and `api_key="abc"` on `app.config.settings`;
  - `GET /api/channels` with `headers=[(b"x-api-key", "é".encode("latin-1"))]` → 401. Today it returns 500.

- [ ] **Step 2: Run them to confirm they fail** (ImportError; then 401 instead of 429, 200 instead of 422, and 500 instead of 401).

- [ ] **Step 3: Implement** as in Interfaces.

- [ ] **Step 4: Run the tests** (pass) and the offline suite.

- [ ] **Step 5: Commit**

```bash
git add backend/app/auth.py backend/app/routers/auth.py README.md backend/tests/test_login.py
git commit -m "feat(auth): rate-limit failed logins and verify passwords off the event loop"
```

### Task 18: Persistent JWT secret and strict claims [S4]

**Files:**
- Modify: `backend/app/config.py` (delete `model_post_init` and the now-unused `secrets` import)
- Modify: `backend/app/auth.py` (`create_access_token`, `verify_token`; add the secret loader)
- Modify: `.env.example` (JWT comment)
- Test: `backend/tests/test_jwt.py`

**Interfaces:**
- Produces: `JWT_SECRET_FILE = Path("data") / ".jwt_secret"` and `get_jwt_secret() -> str`, cached in the module-level `_jwt_secret: str | None`. Precedence:
  1. a non-empty `settings.jwt_secret_key`;
  2. the stripped contents of `JWT_SECRET_FILE`, when it exists and isn't empty;
  3. otherwise generate `secrets.token_urlsafe(32)`, `mkdir(parents=True, exist_ok=True)` the parent, and write with `os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)`. On `FileExistsError`, read the file instead.
- `create_access_token()` signs with `get_jwt_secret()`. `verify_token(token)` decodes with `options={"require": ["exp", "iat"]}` and returns `payload.get("type") == "access"`.
- `.env.example`: "If unset, a secret is generated once and stored in data/.jwt_secret."

- [ ] **Step 1: Write the failing tests.**
- In `tests/conftest.py`, add an autouse fixture that monkeypatches `app.config.settings.jwt_secret_key` to `"test-secret"`, so no other test writes `backend/data/.jwt_secret`.
- In `test_jwt.py`, add an autouse fixture that monkeypatches `app.auth.JWT_SECRET_FILE` to `tmp_path / "data" / ".jwt_secret"`, sets `app.auth._jwt_secret = None`, and sets `app.config.settings.jwt_secret_key = ""`. It runs after the conftest fixture, so it wins.

The tests:
- `test_secret_generated_once_and_persisted`:
  - two calls return the same value;
  - the file holds it;
  - `stat.S_IMODE(file.stat().st_mode) == 0o600`;
  - after `_jwt_secret = None`, the next call returns the same value.
- `test_env_secret_takes_precedence`: `settings.jwt_secret_key = "fixed"` → `"fixed"`, and the file is not created.
- `test_token_roundtrip`: `verify_token(create_access_token())`.
- `test_wrong_type_rejected`: a `jwt.encode` with `"type": "refresh"` plus valid `exp`/`iat` and the same secret is rejected.
- `test_missing_iat_rejected`: a token without `iat` is rejected.

- [ ] **Step 2: Run them to confirm they fail.**

- [ ] **Step 3: Implement** as in Interfaces.

- [ ] **Step 4: Run the tests** (pass) and the offline suite.

- [ ] **Step 5: Commit**

```bash
git add backend/app/config.py backend/app/auth.py .env.example backend/tests/test_jwt.py
git commit -m "feat(auth): persist generated JWT secret and require access-token claims"
```

### Task 19: Hide the API docs when auth is on; add security headers and optional host allow-list [S5, S6, S13]

**Files:**
- Modify: `backend/app/main.py` (the `FastAPI(...)` construction; a middleware; optional `TrustedHostMiddleware`)
- Modify: `backend/app/config.py` (add `allowed_hosts: str = ""`)
- Modify: `.env.example` (document `ALLOWED_HOSTS`)
- Modify: `README.md:129` (docs sentence) and the README authentication section
- Test: `backend/tests/test_app_hardening.py`

**Interfaces:**
- Produces: `api_docs_urls(auth_enabled: bool) -> dict[str, str | None]`. It returns keys `docs_url`, `redoc_url` and `openapi_url`: all `None` when enabled, otherwise `"/docs"`, `"/redoc"` and `"/openapi.json"`. Use `app = FastAPI(lifespan=lifespan, **api_docs_urls(settings.auth_enabled))`.
- An `@app.middleware("http")` function, `add_security_headers`, calls `response.headers.setdefault` for:
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `Referrer-Policy: strict-origin-when-cross-origin`
- README: "Interactive docs are available at `/docs` when authentication is disabled."
- Produces: `parse_allowed_hosts(value: str) -> list[str]` in `main.py`:
  - for an empty or blank value it returns `[]`;
  - otherwise it returns the stripped, non-empty comma-separated entries, plus `"localhost"` and `"127.0.0.1"` if they're missing, so the container healthcheck keeps working.

  If the list is non-empty, call `app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)` (from `starlette.middleware.trustedhost`).
- `.env.example`: `# ALLOWED_HOSTS=watcher.example.com,192.168.1.10   (optional; rejects requests for other Host headers, which blocks DNS-rebinding attacks)`.
- README authentication section: one sentence recommending `AUTH_ENABLED=true` on any network you don't fully trust, and mentioning `ALLOWED_HOSTS`.

- [ ] **Step 1: Write the failing tests:**
- `test_docs_hidden_when_auth_enabled`: every value of `api_docs_urls(True)` is None.
- `test_docs_shown_when_auth_disabled`: `api_docs_urls(False)["docs_url"] == "/docs"`.
- `test_security_headers_present(client)`: `GET /api/health` has all three headers with exactly those values.
- `test_parse_allowed_hosts`:
  - `parse_allowed_hosts("") == []` and `parse_allowed_hosts("  ") == []`;
  - `parse_allowed_hosts("a.example, b.example") == ["a.example", "b.example", "localhost", "127.0.0.1"]`;
  - `parse_allowed_hosts("localhost") == ["localhost", "127.0.0.1"]`.

- [ ] **Step 2: Run them to confirm they fail.**

- [ ] **Step 3: Implement** as in Interfaces.

- [ ] **Step 4: Run the tests** (pass) and the offline suite.

- [ ] **Step 5: Commit**

```bash
git add backend/app/main.py backend/app/config.py .env.example README.md backend/tests/test_app_hardening.py
git commit -m "feat(security): hide API docs when auth is enabled; security headers; optional host allow-list"
```

### Task 20: Validate imported IDs and rebuild every stored URL [S8]

**Files:**
- Modify: `backend/app/services/youtube_utils.py` (add validators)
- Modify: `backend/app/routers/import_export.py` (`import_channels`, `import_videos`)
- Create: `backend/alembic/versions/20261020_1300_d4e5f6a7b8c9_normalize_stored_urls.py`
- Test: `backend/tests/test_import_validation.py`

**Interfaces:**
- Consumes: Task 10's `import_videos` and Task 15's migration head `c3d4e5f6a7b8`.
- Produces, in `youtube_utils`:
  - `VIDEO_ID_RE = re.compile(r"^[A-Za-z0-9_-]{11}$")` and `CHANNEL_ID_RE = re.compile(r"^UC[A-Za-z0-9_-]{22}$")`;
  - `is_valid_video_id(value: str | None) -> bool` and `is_valid_channel_id(value: str | None) -> bool`.
- `import_videos`:
  - an item whose `youtube_video_id` fails validation is not imported, and appends `f"Invalid video ID: {item.youtube_video_id!r}"` to `errors`;
  - `video_url` is always `get_video_url(id)`, ignoring the supplied value;
  - an invalid `channel_youtube_id` is stored as `None`, and `channel_name` is kept.
- `import_channels`:
  - an invalid `youtube_channel_id` appends `f"Invalid channel ID for {name}: {id!r}"`, skips the item, and never calls `fetch_channel_info`;
  - `youtube_url` is always `get_channel_url(id)`.
- The migration has `revision = 'd4e5f6a7b8c9'` and `down_revision = 'c3d4e5f6a7b8'`. `upgrade()` runs:

  ```sql
  UPDATE videos SET video_url = 'https://www.youtube.com/watch?v=' || youtube_video_id
    WHERE video_url NOT LIKE 'https://www.youtube.com/%';
  UPDATE channels SET youtube_url = 'https://www.youtube.com/channel/' || youtube_channel_id
    WHERE youtube_url NOT LIKE 'https://www.youtube.com/%';
  ```

  `downgrade()` is a no-op (`pass`), with a comment that normalization isn't reversible.

- [ ] **Step 1: Write the failing tests.** Patch `app.routers.import_export.fetch_channel_info` with `AsyncMock(return_value=ChannelInfo(channel_id=CID, name="N"))`, where `CID = "UC" + "a" * 22`.
- `test_import_video_ignores_supplied_url`:
  - import an item with `youtube_video_id="h"*11` and `video_url="javascript:alert(1)"`;
  - the stored `video_url == "https://www.youtube.com/watch?v=hhhhhhhhhhh"`.
- `test_import_video_rejects_invalid_id`:
  - `youtube_video_id='x"><img src=x>'`;
  - `imported == 0`, and `errors == ["Invalid video ID: 'x\"><img src=x>'"]`;
  - no row exists.
- `test_import_video_drops_invalid_channel_id`: `channel_youtube_id="not-a-channel"` → stored `None`, and `channel_name` is kept.
- `test_import_channel_ignores_supplied_url`: `{"youtube_channel_id": CID, "name": "N", "youtube_url": "javascript:alert(1)"}` → the stored `youtube_url == f"https://www.youtube.com/channel/{CID}"`.
- `test_import_channel_rejects_invalid_id`: `youtube_channel_id="UCshort"` → error recorded, the fetch mock not awaited, and the channel count is 0.

- [ ] **Step 2: Run them to confirm they fail** (the `javascript:` value is stored verbatim; invalid IDs are imported).

- [ ] **Step 3: Implement** the validators, the router changes and the migration.

- [ ] **Step 4: Verify** the tests and the offline suite pass, then check the migration on a scratch DB (same setup as Task 15 Step 4):

```bash
SCRATCH=$(mktemp -d) && cp -R alembic alembic.ini app "$SCRATCH"/ && mkdir "$SCRATCH/data"
(cd "$SCRATCH" && "$OLDPWD/.venv/bin/alembic" upgrade c3d4e5f6a7b8)
sqlite3 "$SCRATCH/data/youtube-watcher.db" "INSERT INTO videos(id,youtube_video_id,title,video_url,published_at,status,is_short) VALUES('v1','hhhhhhhhhhh','t','javascript:alert(1)','2026-01-01','saved',0);"
(cd "$SCRATCH" && "$OLDPWD/.venv/bin/alembic" upgrade head)
sqlite3 "$SCRATCH/data/youtube-watcher.db" "SELECT video_url FROM videos WHERE id='v1';"
```

Expected: `https://www.youtube.com/watch?v=hhhhhhhhhhh`.

- [ ] **Step 5: Commit**

```bash
git add backend/app/services/youtube_utils.py backend/app/routers/import_export.py backend/alembic/versions/20261020_1300_d4e5f6a7b8c9_normalize_stored_urls.py backend/tests/test_import_validation.py
git commit -m "fix(security): validate imported IDs and rebuild stored YouTube URLs"
```

### Task 21: Safe links in the UI, safe rendering in quickplay.html, clear the API cache on logout [S7, S8, S12]

**Files:**
- Create: `frontend/src/utils/safeUrl.ts`
- Modify: `frontend/src/components/video/VideoCard.tsx` (6 `href={video.video_url}`), `frontend/src/pages/QuickPlay.tsx:97`, `frontend/src/components/channel/ChannelCard.tsx:50`, `frontend/src/components/channel/ChannelListView.tsx:68`
- Modify: `frontend/src/context/AuthContext.tsx` (every `localStorage.removeItem(STORAGE_KEY)` site)
- Modify: `quickplay.html` (`escapeHtml`, `renderVideoList`)

**Interfaces:**
- Produces: `export function safeExternalUrl(url: string | null | undefined): string | undefined`. It returns `url` only if `new URL(url).protocol` is `http:` or `https:`; for anything else, including parse errors, it returns `undefined`.
- Every `href={video.video_url}` becomes `href={safeExternalUrl(video.video_url)}`, and every `href={channel.youtube_url}` becomes `href={safeExternalUrl(channel.youtube_url)}`. Check with `grep -rn "href={video.video_url}\|href={channel.youtube_url}" frontend/src`; expected: no matches.
- `AuthContext.tsx`: add `function clearApiCache(): void`, which calls `caches.delete('api-cache')` when `'caches' in window` (ignoring the promise result). Call it right after each `localStorage.removeItem(STORAGE_KEY)`.
- `quickplay.html`:
  - `escapeHtml(text)` becomes a pure string function that replaces `&` → `&amp;`, `<` → `&lt;`, `>` → `&gt;`, `"` → `&quot;`, `'` → `&#39;` (`&` first), and returns `''` for falsy input;
  - in `renderVideoList`, `href` is `https://www.youtube.com/watch?v=${encodeURIComponent(v.youtube_video_id)}`;
  - `src` is `escapeHtml(v.thumbnail_url)` only when `v.thumbnail_url` starts with `https://`, otherwise `''`.

- [ ] **Step 1: Implement** as in Interfaces.

- [ ] **Step 2: Verify the frontend**

Run: `cd frontend && npx tsc --noEmit && npm run lint`
Expected: tsc exits 0 and lint reports 0 errors.

- [ ] **Step 3: Verify the quickplay.html escaping** (from the repo root):

```bash
node -e "const s=require('fs').readFileSync('quickplay.html','utf8'); eval(s.match(/function escapeHtml[\s\S]*?\n    }/)[0]); const out=escapeHtml('a\"b<c>\'d&'); console.log(out); process.exit(out==='a&quot;b&lt;c&gt;&#39;d&amp;'?0:1)"
grep -n 'href="\${v.video_url}"' quickplay.html
```

Expected: the first command prints `a&quot;b&lt;c&gt;&#39;d&amp;` and exits 0; the grep prints nothing.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/utils/safeUrl.ts frontend/src/components/video/VideoCard.tsx frontend/src/pages/QuickPlay.tsx frontend/src/components/channel/ChannelCard.tsx frontend/src/components/channel/ChannelListView.tsx frontend/src/context/AuthContext.tsx quickplay.html
git commit -m "fix(security): render only http(s) links, escape quotes in quickplay.html, clear API cache on logout"
```

---

## Phase E — Cleanup and finish

### Task 22: Small correctness and maintenance fixes [C8, P8, B5, B6]

**Files:**
- Modify: `backend/app/routers/settings.py`:
  - delete `_ensure_settings_table` and its call;
  - `SettingsUpdate.http_timeout: Optional[float] = Field(default=None, ge=1.0, le=300.0, ...)`.
- Modify: `backend/app/routers/videos.py`: replace the three inline `VideoResponse(...)` blocks (inbox, saved, discarded lists) with `map_video_to_response(video)`.
- Modify: `backend/app/error_handlers.py`: in `generic_exception_handler`, swap `print`/`traceback` for a module logger and `logger.exception("Unexpected error on %s", request.url.path)`.
- Modify: `backend/app/services/backup_scheduler.py`: bare `except:` → `except Exception:`.
- Test: `backend/tests/test_settings_api.py`

- [ ] **Step 1: Write the failing test** `test_partial_settings_update_keeps_timeout(client)`:
- `PUT /api/settings/settings` with `{"http_timeout": 30, "auto_detect_shorts": True}`;
- then `PUT` with `{"auto_detect_shorts": False}`;
- `GET` returns `http_timeout == 30.0` and `auto_detect_shorts is False`.

- [ ] **Step 2: Run it to confirm it fails** (`10.0 != 30.0`).

- [ ] **Step 3: Implement** all four bullets.

- [ ] **Step 4: Run the tests** (pass) and the offline suite. Also run `grep -n "print(" backend/app -r`; expected: no matches in `error_handlers.py`.

- [ ] **Step 5: Commit**

```bash
git add backend/app/routers/settings.py backend/app/routers/videos.py backend/app/error_handlers.py backend/app/services/backup_scheduler.py backend/tests/test_settings_api.py
git commit -m "fix: partial settings updates, log unexpected errors, remove per-request create_all"
```

### Task 23: Serialize API datetimes as UTC [C9]

**Files:**
- Create: `backend/app/schemas/types.py`
- Modify: `backend/app/schemas/video.py` (`VideoResponse`), `backend/app/schemas/channel.py` (`ChannelResponse.last_checked`), `backend/app/schemas/settings.py` (`BackupStatus.last_backup_at`, `RefreshStatus.last_refresh_at`)
- Test: `backend/tests/test_utc_datetimes.py`

**Interfaces:**
- Produces: `UTCDateTime = Annotated[datetime, AfterValidator(ensure_utc)]` and `ensure_utc(value: datetime) -> datetime`. A naive value gets `.replace(tzinfo=timezone.utc)`; an aware one gets `.astimezone(timezone.utc)`.
- Apply it (keeping `Optional[...]` where it already is) to:
  - `VideoResponse.published_at`, `saved_at`, `discarded_at` and `is_short_detected_at`;
  - `ChannelResponse.last_checked`;
  - `BackupStatus.last_backup_at` and `RefreshStatus.last_refresh_at`.

  Leave the export and import schemas unchanged.

- [ ] **Step 1: Write the failing tests:**
- `test_video_datetimes_have_utc_suffix(client, sample_video)`: `GET /api/videos/inbox` → `[0]["published_at"].endswith("Z")`.
- `test_ensure_utc`:
  - `ensure_utc(datetime(2026, 1, 1)).tzinfo == timezone.utc`;
  - `ensure_utc(datetime(2026, 1, 1, 6, tzinfo=timezone(timedelta(hours=6)))) == datetime(2026, 1, 1, tzinfo=timezone.utc)`.

- [ ] **Step 2: Run them to confirm they fail.**

- [ ] **Step 3: Implement** as in Interfaces.

- [ ] **Step 4: Run the tests** (pass), the offline suite, and `cd ../frontend && npx tsc --noEmit` (no frontend changes are expected).

- [ ] **Step 5: Commit**

```bash
git add backend/app/schemas/types.py backend/app/schemas/video.py backend/app/schemas/channel.py backend/app/schemas/settings.py backend/tests/test_utc_datetimes.py
git commit -m "fix: serialize API datetimes as UTC"
```

### Task 24: Documentation and final verification

**Files:**
- Modify: `AGENTS.md`, `DEVELOPER_GUIDE.md`, `README.md`

- [ ] **Step 1: `AGENTS.md`**
- Add a Recent Changes row dated the day you finish, summarizing the security fixes, subscription independence, performance work and the lock file.
- Under Conventions, add:
  - the subscription rule (Global Constraints, first bullet);
  - "Never enable `PRAGMA foreign_keys` (existing DBs have ON DELETE CASCADE)";
  - "Dependencies are pinned in `backend/requirements.lock`".

- [ ] **Step 2: `DEVELOPER_GUIDE.md`**
- §2 Video model: replace "FK to channels table (SET NULL on delete)" with the real behavior — existing SQLite DBs declare CASCADE but foreign keys are off, and the delete endpoint unlinks videos first.
- Update the backups subsection: path is `<database dir>/backups`, made with the SQLite backup API.
- Update the auth subsection: hash format and lockout.

- [ ] **Step 3: `README.md`**
- Replace the `:v2026-04-20` example: tagged releases now publish `:vYYYY-MM-DD` images, starting with the next release.
- Check the auth section matches Tasks 16–21.

- [ ] **Step 4: Full verification**

```bash
cd backend && .venv/bin/python -m pytest -q
.venv/bin/pip-audit --disable-pip --require-hashes -r requirements.lock
cd ../frontend && npx tsc --noEmit && npm run lint
cd .. && docker compose -f docker-compose-local.yml up --build -d
```

Then repeat Task 3 Step 7's checks:
- health returns OK;
- the yt-dlp line prints metadata;
- the container is `healthy`;
- `curl -s --path-as-is 'http://localhost:38000/../data/youtube-watcher.db' | head -c 15` and `curl -s --path-as-is 'http://localhost:38000//etc/passwd' | head -c 15` both print the start of the SPA HTML (`<!doctype html>`), never `SQLite format 3` or `root:`.

Finish with `docker compose -f docker-compose-local.yml down`.

Expected: all tests pass (report integration results separately if there's no network), no vulnerabilities, tsc 0, lint 0 errors.

- [ ] **Step 5: Commit**

```bash
git add AGENTS.md DEVELOPER_GUIDE.md README.md
git commit -m "docs: document backend hardening, subscription rules and dependency lock"
```
