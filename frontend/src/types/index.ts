export interface Channel {
  id: string;
  youtube_channel_id: string;
  name: string;
  youtube_url: string;
  thumbnail_url: string | null;
  last_checked: string | null;
  last_video_id: string | null;
  video_count: number;
  created_at: string;
  updated_at: string;
}

export interface Video {
  id: string;
  youtube_video_id: string;
  channel_id: string | null;
  channel_youtube_id: string | null;
  channel_name: string | null;
  channel_thumbnail_url: string | null;
  title: string;
  description: string | null;
  thumbnail_url: string | null;
  video_url: string;
  published_at: string;
  status: 'inbox' | 'saved' | 'discarded';
  saved_at: string | null;
  discarded_at: string | null;
  is_short: boolean;  // Issue #8: YouTube Shorts detection
}

export interface ChannelFilterOption {
  channel_youtube_id: string;
  channel_name: string;
  channel_thumbnail_url: string | null;
  video_count: number;
}

export interface SavedVideosParams {
  channel_youtube_id?: string;
  sort_by?: 'published_at' | 'saved_at';
  order?: 'asc' | 'desc';
}

// Issue #8: Shorts filter type for inbox
export type ShortsFilter = 'all' | 'shorts' | 'regular';

// Issue #12: Scheduled Backups - Backup-related types
export interface BackupSettings {
  backup_enabled: boolean;
  backup_schedule: 'daily' | 'weekly' | 'monthly';
  backup_time: string;
  backup_format: 'json' | 'database' | 'both';
  backup_retention_days: number;
}

export interface BackupStatus {
  last_backup_at: string | null;
  last_backup_status: 'success' | 'failed' | null;
  last_backup_error: string | null;
}

export interface BackupInfo {
  filename: string;
  format: string;
  size_bytes: number;
  created_at: string;
}

export interface BackupListResponse {
  backups: BackupInfo[];
  total_count: number;
  total_size_bytes: number;
}

export interface ManualBackupResponse {
  success: boolean;
  filenames: string[];
  error: string | null;
}