import { Squares2X2Icon, ListBulletIcon, RectangleStackIcon } from '@heroicons/react/24/outline';
import { segmentedGroup, segmentedItem } from './segmented';

export type ViewMode = 'large' | 'compact' | 'list';

interface ViewModeToggleProps {
  viewMode: ViewMode;
  onChange: (mode: ViewMode) => void;
}

const modes: { value: ViewMode; icon: typeof Squares2X2Icon; label: string }[] = [
  { value: 'list', icon: ListBulletIcon, label: 'List' },
  { value: 'compact', icon: Squares2X2Icon, label: 'Compact' },
  { value: 'large', icon: RectangleStackIcon, label: 'Large' },
];

export default function ViewModeToggle({ viewMode, onChange }: ViewModeToggleProps) {
  return (
    <div className={segmentedGroup} role="group" aria-label="View mode">
      {modes.map(({ value, icon: Icon, label }) => (
        <button
          key={value}
          onClick={() => onChange(value)}
          className={segmentedItem(viewMode === value)}
          aria-pressed={viewMode === value}
          title={`${label} view`}
        >
          <Icon className="w-4 h-4" />
          <span className="hidden sm:inline">{label}</span>
        </button>
      ))}
    </div>
  );
}
