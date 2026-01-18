import { Video } from '../types';

const MAX_PLAYLIST_VIDEOS = 50;
const YOUTUBE_WATCH_VIDEOS_URL = 'https://www.youtube.com/watch_videos';

export interface PlaylistResult {
  url: string;
  videoCount: number;
  truncated: boolean;
}

/**
 * Generates a YouTube playlist URL from an array of videos.
 * YouTube's watch_videos endpoint supports up to ~50 videos.
 */
export function generatePlaylistUrl(videos: Video[]): PlaylistResult {
  const truncated = videos.length > MAX_PLAYLIST_VIDEOS;
  const videosToInclude = videos.slice(0, MAX_PLAYLIST_VIDEOS);

  const videoIds = videosToInclude.map(v => v.youtube_video_id).join(',');
  const url = `${YOUTUBE_WATCH_VIDEOS_URL}?video_ids=${videoIds}`;

  return {
    url,
    videoCount: videosToInclude.length,
    truncated,
  };
}

/**
 * Opens the playlist URL in a new tab.
 */
export function openPlaylist(videos: Video[]): PlaylistResult {
  const result = generatePlaylistUrl(videos);
  window.open(result.url, '_blank', 'noopener,noreferrer');
  return result;
}
