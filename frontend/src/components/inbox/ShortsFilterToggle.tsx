import type { ShortsFilter } from '../../types';
import { segmentedGroup, segmentedItem } from '../common/segmented';

interface ShortsFilterToggleProps {
  value: ShortsFilter;
  onChange: (value: ShortsFilter) => void;
}

const options: { value: ShortsFilter; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'regular', label: 'Videos' },
  { value: 'shorts', label: 'Shorts' },
];

export function ShortsFilterToggle({ value, onChange }: ShortsFilterToggleProps) {
  return (
    <div className={segmentedGroup} role="group" aria-label="Filter by type">
      {options.map((option) => (
        <button
          key={option.value}
          onClick={() => onChange(option.value)}
          className={segmentedItem(value === option.value)}
          aria-pressed={value === option.value}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
