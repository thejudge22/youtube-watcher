import { ListBulletIcon, RectangleGroupIcon } from '@heroicons/react/24/outline';
import { segmentedGroup, segmentedItem } from '../common/segmented';

export type InboxViewMode = 'flat' | 'grouped';

interface InboxViewToggleProps {
  viewMode: InboxViewMode;
  onChange: (mode: InboxViewMode) => void;
}

export function InboxViewToggle({ viewMode, onChange }: InboxViewToggleProps) {
  return (
    <div className={segmentedGroup} role="group" aria-label="Inbox layout">
      <button
        onClick={() => onChange('flat')}
        className={segmentedItem(viewMode === 'flat')}
        aria-pressed={viewMode === 'flat'}
        title="Flat view"
      >
        <ListBulletIcon className="w-4 h-4" />
        <span>Flat</span>
      </button>
      <button
        onClick={() => onChange('grouped')}
        className={segmentedItem(viewMode === 'grouped')}
        aria-pressed={viewMode === 'grouped'}
        title="Grouped by channel"
      >
        <RectangleGroupIcon className="w-4 h-4" />
        <span>Grouped</span>
      </button>
    </div>
  );
}
