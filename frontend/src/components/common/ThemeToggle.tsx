import { SunIcon, MoonIcon } from '@heroicons/react/24/outline';
import type { Theme } from '../../hooks/useTheme';

interface ThemeToggleProps {
  theme: Theme;
  onToggle: () => void;
}

export function ThemeToggle({ theme, onToggle }: ThemeToggleProps) {
  const isDark = theme === 'dark';

  return (
    <button
      onClick={onToggle}
      className="relative p-2 rounded-lg transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-accent-blue focus:ring-offset-2 focus:ring-offset-bg-primary hover:bg-bg-tertiary"
      title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
      aria-label={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
    >
      <div className="relative w-5 h-5">
        {/* Sun Icon */}
        <SunIcon
          className={`w-5 h-5 absolute inset-0 transition-all duration-200 ${
            isDark
              ? 'opacity-0 rotate-90 scale-0'
              : 'opacity-100 rotate-0 scale-100 text-accent-orange'
          }`}
        />
        {/* Moon Icon */}
        <MoonIcon
          className={`w-5 h-5 absolute inset-0 transition-all duration-200 ${
            isDark
              ? 'opacity-100 rotate-0 scale-100 text-accent-blue'
              : 'opacity-0 -rotate-90 scale-0'
          }`}
        />
      </div>
    </button>
  );
}
