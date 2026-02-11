import axios from 'axios';
import type { Channel, Video, SavedVideosParams, ChannelFilterOption, PaginatedVideosResponse } from '../types';

// Default timeout for most requests
const DEFAULT_TIMEOUT = 30000; // 30 seconds

// Extended timeout for long-running operations like imports
const LONG_TIMEOUT = 300000; // 5 minutes

// API client with explicit configuration to ensure consistent behavior
const api = axios.create({
  baseURL: '/api',
  headers: {
    'Content-Type': 'application/json', // Explicitly set JSON content type
    'Accept': 'application/json', // Explicitly request JSON responses
  },
  timeout: DEFAULT_TIMEOUT,
});

// Issue #41: Optional Authentication - Token storage
let authToken: string | null = null;

/**
 * Set the authentication token for API requests
 */
export function setAuthToken(token: string): void {
  authToken = token;
}

/**
 * Clear the authentication token
 */
export function clearAuthToken(): void {
  authToken = null;
}

// Request interceptor to add auth token
api.interceptors.request.use(
  (config) => {
    if (authToken) {
      config.headers.Authorization = `Bearer ${authToken}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Settings types
export interface AppSettings {
  http_timeout: number;
}

// Add response interceptor to handle structured error responses
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle structured error responses from backend
    if (error.response?.data?.error) {
      const { code, message, details } = error.response.data.error;
      // Attach structured error info to the error object for easier handling
      error.errorCode = code;
      error.errorMessage = message;
      error.errorDetails = details;
    }
    return Promise.reject(error);
  }
);

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
    channel_url: string | null;
    saved_at: string | null;
    published_at: string | null;
  }>;
}

// Issue #41: Optional Authentication - Auth types
export interface AuthStatus {
  enabled: boolean;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  token: string;
  token_type: string;
}

export interface TokenVerifyRequest {
  token: string;
}

export interface TokenVerifyResponse {
  valid: boolean;
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
  getInbox: (channelId?: string, isShort?: boolean | null) =>
    api.get<Video[]>('/videos/inbox', {
      params: {
        ...(channelId ? { channel_id: channelId } : {}),
        ...(isShort !== undefined && isShort !== null ? { is_short: isShort } : {})
      }
    }),
  getSaved: (params?: SavedVideosParams) => api.get<PaginatedVideosResponse>('/videos/saved', { params }),
  getSavedChannels: () => api.get<ChannelFilterOption[]>('/videos/saved/channels'),
  getDiscarded: (days?: number) => api.get<Video[]>('/videos/discarded', { params: { days } }),
  save: (id: string) => api.post<Video>(`/videos/${id}/save`),
  discard: (id: string) => api.post<Video>(`/videos/${id}/discard`),
  bulkSave: (videoIds: string[]) => api.post<Video[]>('/videos/bulk-save', { video_ids: videoIds }),
  bulkDiscard: (videoIds: string[]) => api.post<Video[]>('/videos/bulk-discard', { video_ids: videoIds }),
  fromUrl: (url: string) => api.post<Video>('/videos/from-url', { url }),
  delete: (id: string) => api.delete(`/videos/${id}`),
  purgeAllDiscarded: () => api.delete<{ deleted_count: number; message: string }>('/videos/discarded/purge-all'),
  // Issue #8: Shorts detection endpoints
  detectShort: (videoId: string) => api.post<Video>(`/videos/${videoId}/detect-short`),
  detectShortsBatch: (videoIds?: string[]) => api.post<{ total_checked: number; updated_count: number }>('/videos/detect-shorts-batch', { video_ids: videoIds }),
};

// Import/Export API
export const importExportApi = {
  // Export endpoints - these return file downloads
  exportChannels: () => api.get<ExportData>('/import-export/export/channels'),
  exportSavedVideos: () => api.get<ExportData>('/import-export/export/saved-videos'),
  exportAll: () => api.get<ExportData>('/import-export/export/all'),

  // Import endpoints - use extended timeout for long-running operations
  importChannels: (channels: ExportData['channels']) =>
    api.post<ImportResult>('/import-export/import/channels', { channels }, { timeout: LONG_TIMEOUT }),

  importVideos: (videos: ExportData['saved_videos']) =>
    api.post<ImportResult>('/import-export/import/videos', { videos }, { timeout: LONG_TIMEOUT }),

  importVideoUrls: (urls: string[]) =>
    api.post<ImportResult>('/import-export/import/video-urls', { urls }, { timeout: LONG_TIMEOUT }),

  importPlaylist: (url: string) =>
    api.post<ImportResult>('/import-export/import/playlist', { url }, { timeout: LONG_TIMEOUT }),
};

// Settings API
export const settingsApi = {
  get: () => api.get<AppSettings>('/settings/settings'),
  update: (settings: Partial<AppSettings>) => api.put<AppSettings>('/settings/settings', settings),
};

// Issue #12: Scheduled Backups - Backup API
export const backupApi = {
  getSettings: () => api.get<any>('/backup/settings'),
  updateSettings: (settings: any) => api.put<any>('/backup/settings', settings),
  getStatus: () => api.get<any>('/backup/status'),
  listBackups: () => api.get<any>('/backup/list'),
  runBackup: (format: string = 'json') => api.post<any>('/backup/run', { format }),
  cleanup: () => api.delete('/backup/cleanup'),
};

// Issue #41: Optional Authentication - Auth API
export const authApi = {
  /** Check if authentication is enabled */
  getStatus: () => api.get<AuthStatus>('/auth/status'),
  
  /** Log in with username and password */
  login: (username: string, password: string) =>
    api.post<LoginResponse>('/auth/login', { username, password }),
  
  /** Verify if a token is still valid */
  verifyToken: (token: string) =>
    api.post<TokenVerifyResponse>('/auth/verify', { token }),
  
  /** Log out (client-side token removal) */
  logout: () => api.post('/auth/logout'),
};
