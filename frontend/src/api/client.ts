import axios from 'axios';
import type { Channel, Video, SavedVideosParams } from '../types';

const api = axios.create({
  baseURL: '/api',
});

// Response types based on API responses
interface RefreshSummary {
  channels_refreshed: number;
  new_videos_found: number;
  errors: string[];
}

export interface ImportResult {
  total: number;
  imported: number;
  skipped: number;
  errors: string[];
}

export interface ExportData {
  version: string;
  exported_at: string;
  channels: Array<{
    youtube_channel_id: string;
    name: string;
    youtube_url: string;
  }>;
  saved_videos: Array<{
    youtube_video_id: string;
    title: string;
    video_url: string;
    channel_youtube_id: string | null;
    channel_name: string | null;
    saved_at: string | null;
    published_at: string | null;
  }>;
}

// Channel API
export const channelsApi = {
  list: () => api.get<Channel[]>('/channels'),
  create: (url: string) => api.post<Channel>('/channels', { url }),
  delete: (id: string) => api.delete(`/channels/${id}`),
  refresh: (id: string) => api.post<Channel>(`/channels/${id}/refresh`),
  refreshAll: () => api.post<RefreshSummary>('/channels/refresh-all'),
};

// Video API
export const videosApi = {
  getInbox: (channelId?: string) =>
    api.get<Video[]>('/videos/inbox', {
      params: channelId ? { channel_id: channelId } : undefined
    }),
  getSaved: (params?: SavedVideosParams) => api.get<Video[]>('/videos/saved', { params }),
  getDiscarded: (days?: number) => api.get<Video[]>('/videos/discarded', { params: { days } }),
  save: (id: string) => api.post<Video>(`/videos/${id}/save`),
  discard: (id: string) => api.post<Video>(`/videos/${id}/discard`),
  bulkSave: (videoIds: string[]) => api.post<Video[]>('/videos/bulk-save', { video_ids: videoIds }),
  bulkDiscard: (videoIds: string[]) => api.post<Video[]>('/videos/bulk-discard', { video_ids: videoIds }),
  fromUrl: (url: string) => api.post<Video>('/videos/from-url', { url }),
  delete: (id: string) => api.delete(`/videos/${id}`),
  purgeAllDiscarded: () => api.delete<{ deleted_count: number; message: string }>('/videos/discarded/purge-all'),
};

// Import/Export API
export const importExportApi = {
  // Export endpoints - these return file downloads
  exportChannels: () => api.get<ExportData>('/import-export/export/channels'),
  exportSavedVideos: () => api.get<ExportData>('/import-export/export/saved-videos'),
  exportAll: () => api.get<ExportData>('/import-export/export/all'),

  // Import endpoints
  importChannels: (channels: ExportData['channels']) =>
    api.post<ImportResult>('/import-export/import/channels', { channels }),

  importVideos: (videos: ExportData['saved_videos']) =>
    api.post<ImportResult>('/import-export/import/videos', { videos }),

  importVideoUrls: (urls: string[]) =>
    api.post<ImportResult>('/import-export/import/video-urls', { urls }),
};