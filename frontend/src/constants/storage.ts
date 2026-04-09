// Storage namespace prefix to prevent collisions with other apps
export const STORAGE_PREFIX = 'youtube-watcher:';

// Storage keys used throughout the application
export const STORAGE_KEYS = {
  INBOX_VIEW_MODE: 'inbox-view-mode',
  SAVED_VIEW_MODE: 'saved-view-mode',
  THEME: 'theme',
} as const;

// Helper function to get the full namespaced key
export function getStorageKey(key: string): string {
  return `${STORAGE_PREFIX}${key}`;
}
