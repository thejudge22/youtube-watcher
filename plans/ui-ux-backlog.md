# UI/UX Backlog

Review of the frontend done 2026-10-20. Not scheduled; each item is a candidate for its own spec.
The app is used equally on desktop and phone (PWA), and native mobile apps (separate project) call the same API, so any API change must stay backward compatible.

## Redundant or confusing

1. **Inconsistent vocabulary.** Discard (Inbox), Remove (Saved, QuickPlay), Delete (channel tooltip), Unsubscribe (channel confirm), Recently Deleted. The restore button in Recently Deleted is labelled "Save". Pick one verb per action: Discard / Remove from library / Unsubscribe / Restore.
2. **Inverted confirmations.** Removing one saved video opens a modal; "Remove Selected" in Saved and "Discard All" in Inbox (the whole inbox) have none. Replace with an Undo toast; the app has no toast system yet.
3. **Recently Deleted is buried and its "30 days" is misleading.** It is a modal reachable only from Saved, although Inbox discards and unsubscribes also land there. Purge lives in Settings behind a Show/Hide toggle. "30 days" is only the list's look-back window (`GET /api/videos/discarded?days=30`); nothing is ever purged automatically, so older discards become invisible but stay in the database. Give it a page/tab with Restore and Purge and either real auto-purge or no retention claim.
4. **"Refresh" means different things.** Inbox Refresh fetches RSS feeds; QuickPlay Refresh only re-reads the DB; Settings → Auto-Refresh has its own manual refresh; each channel card has another.
5. **"Detect Shorts" toolbar buttons** on Inbox and Saved, although the Auto-Detect Shorts setting is on by default. Move to Settings/maintenance.
6. **Three view toggles.** Inbox Flat/Grouped (cards always large), Saved List/Compact/Large, Channels Grid/List (hand-rolled localStorage). Different look and behaviour; unify into one component and let Inbox use the card sizes.
7. **QuickPlay "Play All" drops Shorts.** It merges up to 50 videos and 50 Shorts, then `openPlaylist` truncates to 50. Truncation is only `console.log`ged (also in Saved's Play as Playlist). Tell the user, or drop Play All.
8. **Settings page.** Dead "Remove all saved videos" modal (nothing opens it; would only remove the first 100); the page fetches 100 saved videos just for it. Nested cards inside cards, inconsistent heading sizes, a Save button per section, `alert()` for validation.
9. **Two Add entry points.** Header "Add URL" saves a video; "Add Channel" is on the Channels page. One "paste any YouTube URL" box could subscribe to channel URLs and save video URLs.

## UX gaps

10. **Touch:** channel card actions appear only on hover, so they are unreachable on phones.
11. **Narrow screens:** five icon+label nav tabs have no compact layout; the Inbox header holds up to 8 controls that wrap untidily.
12. **Saved filters split:** Shorts filter in the header, channel and sort in a separate panel. Sort and channel filter are not remembered; Shorts filter and view mode are.
13. **Inbox empty state** always says "Add some channels", even when the user has channels and is simply caught up.
14. **Channel card "online" green dot** means nothing.
15. **Triage speed:** no keyboard shortcuts (e.g. `s` save, `d` discard, `j`/`k` move) and no optimistic removal.
16. **QuickPlay selective remove.** Today the only options are removing the whole batch of 50 or going to Saved to remove a few. Proposed design (requested 2026-10-20, not yet approved for build):
    - A **Select** button in each panel header (videos and Shorts select independently).
    - In selection mode, rows show checkboxes and a click toggles the row instead of opening YouTube; shift-click selects a range; on phones, drag along the checkboxes (reuse `useTouchDragSelect` from Saved).
    - The panel header shows "N selected", Select all, Clear, **Remove selected** and Cancel; Play and Remove 50 are hidden while selecting.
    - Remove confirms, moves the items to Recently Deleted (`bulkDiscard`), reloads that panel so the next oldest items fill in, and leaves selection mode.
    - Frontend only (`pages/QuickPlay.tsx`, possibly the touch-select hook); no API change.
    - Open question: also offer **Play selected**?

## Done in the 2026-10-20 visual refresh

- Item 10: channel card actions are always visible on devices without hover.
- Item 11 (nav part): sidebar on desktop, bottom tab bar on phones. The Inbox toolbar still wraps on phones.
- Item 14: the green dot is gone.
- Hard-coded colours that broke light mode now use theme tokens.
- Inbox channel groups no longer nest buttons inside a button.
- Recently Deleted modal uses the list layout instead of a cramped grid.
- Item 6 (look only): all view toggles share one segmented style; behaviour is unchanged.

Still open, seen while testing: the Saved channel filter renders duplicate React keys (two channel options share a `channel_youtube_id`).

## Suggested groupings

- **A. Consistency pass:** items 1, 2, 6, 8 (+ toast system).
- **B. Recently Deleted page + retention:** item 3.
- **C. Mobile pass:** items 10, 11.
- **D. Triage speed:** item 15.
- **E. Unified Add:** item 9.
- **F. QuickPlay selective remove:** item 16.
