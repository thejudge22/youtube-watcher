import { useEffect, useCallback } from 'react';
import { useLocalStorage } from './useLocalStorage';
import { STORAGE_KEYS } from '../constants/storage';

export type Theme = 'dark' | 'light';

// Get system preferred theme
function getSystemTheme(): Theme {
  if (window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches) {
    return 'dark';
  }
  return 'light';
}

export function useTheme(): {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
} {
  const [theme, setThemeState] = useLocalStorage<Theme>(
    STORAGE_KEYS.THEME,
    getSystemTheme()
  );

  // Apply theme to document
  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
  }, [theme]);

  // Listen to system theme changes (if user hasn't explicitly set a preference)
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
    const handleChange = (e: MediaQueryListEvent) => {
      // Only update if user hasn't set an explicit preference
      const storedTheme = localStorage.getItem(`youtube-watcher:${STORAGE_KEYS.THEME}`);
      if (!storedTheme) {
        setThemeState(e.matches ? 'dark' : 'light');
      }
    };

    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, [setThemeState]);

  const toggleTheme = useCallback(() => {
    setThemeState(theme === 'dark' ? 'light' : 'dark');
  }, [setThemeState, theme]);

  const setTheme = useCallback(
    (newTheme: Theme) => {
      setThemeState(newTheme);
    },
    [setThemeState]
  );

  return { theme, toggleTheme, setTheme };
}
