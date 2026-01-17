import { ListBulletIcon, RectangleStackIcon } from '@heroicons/react/24/outline';

export type InboxViewMode = 'flat' | 'grouped';

interface InboxViewToggleProps {
  viewMode: InboxViewMode;
  onChange: (mode: InboxViewMode) => void;
}

export function InboxViewToggle({ viewMode, onChange }: InboxViewToggleProps) {
  return (
    <div className="flex rounded-lg overflow-hidden border border-gray-600">
      <button
        onClick={() => onChange('flat')}
        className={`flex items-center gap-1 px-3 py-1.5 text-sm transition-colors ${
          viewMode === 'flat'
            ? 'bg-gray-600 text-white'
            : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
        }`}
        title="Flat view"
      >
        <ListBulletIcon className="w-4 h-4" />
        <span>Flat</span>
      </button>
      <button
        onClick={() => onChange('grouped')}
        className={`flex items-center gap-1 px-3 py-1.5 text-sm transition-colors ${
          viewMode === 'grouped'
            ? 'bg-gray-600 text-white'
            : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
        }`}
        title="Grouped by channel"
      >
        <RectangleStackIcon className="w-4 h-4" />
        <span>Grouped</span>
      </button>
    </div>
  );
}
