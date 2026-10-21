# Native Client Support (backend side)

**Created:** 2026-10-21, from the native-client compatibility audit of `v2026-10-21`. The report lives with the apps' planning docs (`QuickPlayNativeAppsPlans/COMPATIBILITY_2026-10-21.md` in the QuickPlayClient folder).
**Goal:** the macOS/iPhone/iPad and Android apps get the same priority as the web app. Backend changes can't break them silently, and the shared screens stay in step.
**Status (2026-10-21):** N1, N4 and N6 are done. N2 isn't needed. N3 is open. N5 needs a decision.

The client-side plans are in `QuickPlayNativeAppsPlans/plans/`. The rules this plan enforces are in [docs/native-clients.md](../docs/native-clients.md).

| ID | Item | Priority | API change | Status |
|---|---|---|---|---|
| N1 | Native-client contract test in pytest (and so in CI) | P1 | None | **Done:** `backend/tests/test_native_client_contract.py` (27 tests, offline suite) |
| N2 | A way to check an API key without guessing an endpoint | P3 | Additive | **Not needed:** the 1.1 apps check the key with `GET /api/videos/saved?limit=1`, which works on every server version |
| N3 | Restore a discarded video to the Inbox (for Undo) | P3 | Additive | Open |
| N4 | Keep `DELETE /api/videos/{id}` until both apps use `bulk-discard` | Note | None | The 1.1 apps no longer call it. Keep it until older installs are gone |
| N5 | Put the native contract and plans under version control | P2 | None | **Decision needed:** this repo is public, so moving the native docs here would publish them (see below) |
| N6 | Native-client step in the release workflow | P2 | None | **Done:** added to the release convention in `AGENTS.md` |

---

## N1. Contract test (P1)

Add `backend/tests/test_native_client_contract.py`. It uses the existing `client` fixture and factories to call exactly the requests the apps send (the table in [docs/native-clients.md](../docs/native-clients.md#what-they-call)) and asserts:

- Status codes: 200 for each GET and POST, 201 then 200 for repeated `from-url` with the YouTube fetch mocked, 204 for DELETE.
- Key sets and types: every `Video` field the apps decode is present, with the right JSON type and nullability. Same for `PaginatedVideosResponse`, `RefreshSummary` (with `errors` as a list) and the health response (`version` and `api_version` as strings, `api_version == "1"`).
- Caps: `inbox?limit=10000` and `saved?limit=50` are accepted.
- Auth, with `AUTH_ENABLED` on: `X-API-Key` with the right key passes; a missing or wrong key returns 401 with `error.code == "UNAUTHORIZED"`; `/api/health` and `/api/auth/status` return 200 without a key.
- Datetimes end in `Z`.

The test belongs in the default offline run (`-m "not integration"`), so CI's test gate covers it. If a future change makes it fail, that change needs the steps in docs/native-clients.md rule 6, not an edited test.

## N2. API key check (P3)

`/api/health` is deliberately unauthenticated, so the apps can't use it to tell a good key from a bad one. They'll probe `GET /api/videos/saved?limit=1` instead (client plan S2), which works today. If a cleaner check is wanted, add an optional field to `GET /api/auth/status`, for example `{"enabled": true, "authenticated": false}`, computed from the request's `X-API-Key` or Bearer token. It's additive, so the web app is unaffected.

## N3. Restore to the Inbox (P3)

Undo after a discard can't be done today: `POST /videos/{id}/save` moves the video to Saved, and nothing moves it back to `inbox`. Add `POST /api/videos/bulk-restore-inbox` with `{"video_ids": [...]}`, which sets `status='inbox'` and clears `discarded_at` and `saved_at`. The web app's Undo toast (UI backlog item 2) and the native apps (client plan S10) would both use it.

## N4. Keep DELETE (note)

Both native apps call `DELETE /api/videos/{id}` from QuickPlay delete mode. Client plan S1 switches them to `bulk-discard`. Don't remove or change DELETE until both apps have shipped that change and been updated on the devices in use.

## N5. Version control for the native contract (P2, decision needed)

`QuickPlayClient/` is an umbrella folder, not a git repository. So `API_SPEC.md`, the fixtures, the design system and the native plans have no history and no remote. The options:

1. **Move `QuickPlayNativeAppsPlans/` into this repo** as `docs/native/`. The contract would change in the same commit as the API. But **this repository is public on GitHub**, so the next push would publish the native apps' internal plans and handoff notes. The fixtures are already sample data.
2. **Make `QuickPlayNativeAppsPlans/` its own private repo** on the LAN Gitea, next to the two app repos. Recommended now that the public-repo issue is known. The contract test (N1) and `docs/native-clients.md` already keep the backend side of the guarantee in this repo.

Not done yet: option 1 publishes content, and option 2 creates and pushes a repo, so either one is your call.

## N6. Release workflow (P2)

Add to the "Version Release Workflow" convention in `AGENTS.md`: before tagging, run the native-client checklist in `QuickPlayNativeAppsPlans/API_SYNC_PROCESS.md` § Backend release. That means re-capturing the fixtures, a short smoke test of each app, and a row in the compatibility log. Mention any native-client follow-ups in the release's Recent Changes row.
