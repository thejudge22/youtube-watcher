import type { ShortsFilter } from '../../types';

interface ShortsFilterToggleProps {
  value: ShortsFilter;
  onChange: (value: ShortsFilter) => void;
}

export function ShortsFilterToggle({ value, onChange }: ShortsFilterToggleProps) {
  return (
    <div className="flex items-center space-x-1 bg-gray-700 rounded-lg p-1">
      <button
        onClick={() => onChange('all')}
        className={`px-3 py-1 text-sm rounded-md transition-colors ${
          value === 'all'
            ? 'bg-blue-600 text-white'
            : 'text-gray-300 hover:text-white hover:bg-gray-600'
        }`}
      >
        All
      </button>
      <button
        onClick={() => onChange('regular')}
        className={`px-3 py-1 text-sm rounded-md transition-colors ${
          value === 'regular'
            ? 'bg-blue-600 text-white'
            : 'text-gray-300 hover:text-white hover:bg-gray-600'
        }`}
      >
        Videos
      </button>
      <button
        onClick={() => onChange('shorts')}
        className={`px-3 py-1 text-sm rounded-md transition-colors flex items-center ${
          value === 'shorts'
            ? 'bg-red-600 text-white'
            : 'text-gray-300 hover:text-white hover:bg-gray-600'
        }`}
      >
        <svg
          className="w-3 h-3 mr-1"
          viewBox="0 0 24 24"
          fill="currentColor"
        >
          <path d="M10 15l5.19-3L10 9v6m11.56-7.83c.13.47.22 1.1.28 1.9.07.8.1 1.49.1 2.09L22 12c0 2.19-.16 3.8-.44 4.83-.25.9-.83 1.48-1.73 1.73-.47.13-1.33.22-2.65.28-1.3.07-2.49.1-3.59.1L12 19c-4.19 0-6.8-.16-7.83-.44-.9-.25-1.48-.83-1.73-1.73-.13-.47-.22-1.1-.28-1.9-.07-.8-.1-1.49-.1-2.09L2 12c0-2.19.16-3.8.44-4.83.25-.9.83-1.48 1.73-1.73.47-.13 1.33-.22 2.65-.28 1.3-.07 2.49-.1 3.59-.1L12 5c4.19 0 6.8.16 7.83.44.9.25 1.48.83 1.73 1.73z"/>
        </svg>
        Shorts
      </button>
    </div>
  );
}
