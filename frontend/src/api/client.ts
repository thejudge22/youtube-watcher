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
  getInbox: () => api.get<Video[]>('/videos/inbox'),
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