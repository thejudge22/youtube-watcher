# User Guide

How each part of YouTube-Watcher works. For installation, see the [README](../README.md). For environment variables and login, see [Configuration](configuration.md).

On a computer, the pages are in the sidebar on the left. On a phone, they're in the tab bar at the bottom.

## Channels

Channels are the YouTube channels you follow. New uploads from them appear in your Inbox.

- **Add a channel:** choose **Add Channel** and paste a link to the channel or to one of its videos. See [Supported links](#supported-links).
- **Refresh a channel:** use the refresh button on its card to check it for new videos now.
- **Unsubscribe:** use the delete button on its card. Videos you already saved stay in your library. Videos still waiting in the Inbox move to Recently Deleted.
- **Layout:** switch between grid and list with the toggle at the top.

## Inbox

New videos from your channels land here until you decide what to do with them.

- **Save** moves a video to your Saved library. **Discard** moves it to Recently Deleted.
- **Save All** and **Discard All** at the top act on everything shown. Each channel group also has its own **Save All** and **Discard All**.
- **All / Videos / Shorts** filters by type.
- **Flat / Grouped** shows one list or one section per channel.
- **Refresh** checks every channel for new videos now.
- **Detect Shorts** checks any videos not yet classified as Shorts. With auto-detect on (the default), new videos are classified as they arrive.

## Saved

Your watch-later library.

- **Filter and sort:** pick a channel, sort by published or saved date, and filter by videos or Shorts.
- **Layout:** Large, Compact or List.
- **Select Videos** turns on selection. Click to select, shift-click to select a range, or on a phone drag down the checkboxes. Then choose:
  - **Play as Playlist** opens the selection as a YouTube playlist (up to 50 videos).
  - **Remove Selected** moves the selection to Recently Deleted.
- **Remove** on a single video moves it to Recently Deleted after you confirm.
- **Recently Deleted** opens the list of removed and discarded videos. Choose **Save** on one to restore it.

## QuickPlay

A quick way to work through your oldest saved items.

- The two panels show your 50 oldest saved videos and your 50 oldest saved Shorts.
- **Play Videos** or **Play Shorts** opens that panel's list as a YouTube playlist.
- **Remove 50** moves that panel's batch to Recently Deleted (you can restore them there), then loads the next 50 oldest.

## Adding a single video

Choose **Add URL** (sidebar on a computer, **Add** at the top on a phone) and paste a video link. The video goes straight into your Saved library. This doesn't subscribe you to the channel.

## Recently Deleted

Discarded and removed videos are kept here so you can change your mind. Open it from the **Saved** page. The list shows the last 30 days. To permanently delete everything in it, go to **Settings → Data Management → Data Removal → Purge All**.

## Settings

- **Application Settings:** auto-detect Shorts, and the HTTP timeout used when contacting YouTube. Raise the timeout if adding channels or refreshing often times out.
- **Auto-Refresh:** check all channels every hour, 6 hours, 12 hours or day, and see when the last refresh ran.
- **Scheduled Backups:** daily, weekly or monthly backups as a JSON export, a copy of the database, or both, kept for 7 to 90 days. Backups are saved in `data/backups`. You can also run one now.
- **Import / Export:** see below.
- **Data Management:** permanently purge Recently Deleted.

### Import and export

- **Export** your channels, your saved videos, or everything, as JSON.
- **Import** from:
  - a JSON export (channels, videos, or both);
  - a text file with one YouTube video link per line;
  - a YouTube playlist link.

Importing channels subscribes you to them. Importing videos adds them to Saved without subscribing to their channels. A link-list file can hold up to 1,000 links.

## Installing as an app

YouTube-Watcher can be installed as an app (PWA). On a phone, use your browser's **Add to Home Screen**. On a computer, use the install icon in the address bar. When a new version is available, the app offers a **Reload** button.

## Supported links

| Type | Example |
|------|---------|
| Channel handle | `https://youtube.com/@JoshuaWeissman` |
| Channel ID | `https://youtube.com/channel/UC_x5XG1OV2P6uZZ5FSM9Ttw` |
| Custom channel URL | `https://youtube.com/c/SomeChannel` |
| Video | `https://youtube.com/watch?v=dQw4w9WgXcQ` |
| Short | `https://youtube.com/shorts/mccyHdidiG8` |
| Short link | `https://youtu.be/dQw4w9WgXcQ` |
