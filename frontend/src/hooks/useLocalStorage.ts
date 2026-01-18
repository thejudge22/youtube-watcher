import { useState, useEffect } from 'react';
import { STORAGE_PREFIX } from '../constants/storage';

// Helper to get namespaced key
function getNamespacedKey(key: string): string {
  // If key already has the prefix, don't add it again
  if (key.startsWith(STORAGE_PREFIX)) {
    return key;
  }
  return `${STORAGE_PREFIX}${key}`;
}

// Helper to migrate old key to new namespaced key
function migrateKey(oldKey: string, newKey: string): void {
  try {
    const oldValue = localStorage.getItem(oldKey);
    if (oldValue !== null && localStorage.getItem(newKey) === null) {
      localStorage.setItem(newKey, oldValue);
      localStorage.removeItem(oldKey);
    }
  } catch {
    // Ignore migration errors
  }
}

export function useLocalStorage<T>(key: string, defaultValue: T): [T, (value: T) => void] {
  const namespacedKey = getNamespacedKey(key);

  const [value, setValue] = useState<T>(() => {
    try {
      // Try namespaced key first
      let saved = localStorage.getItem(namespacedKey);

      // Fall back to old key for migration support
      if (saved === null) {
        saved = localStorage.getItem(key);
      }

      return saved ? JSON.parse(saved) : defaultValue;
    } catch {
      return defaultValue;
    }
  });

  // Run migration on first use
  useEffect(() => {
    migrateKey(key, namespacedKey);
  }, [key, namespacedKey]);

  useEffect(() => {
    try {
      localStorage.setItem(namespacedKey, JSON.stringify(value));
    } catch {
      // Ignore localStorage errors
    }
  }, [namespacedKey, value]);

  return [value, setValue];
}
