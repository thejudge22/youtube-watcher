// Shared look for the small segmented toggles (filters, view modes).
export const segmentedGroup =
  'flex items-center gap-0.5 bg-bg-tertiary rounded-lg p-0.5 border border-border';

export function segmentedItem(isActive: boolean) {
  return `flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-md transition-colors ${
    isActive
      ? 'bg-bg-secondary text-text-primary shadow-sm'
      : 'text-text-secondary hover:text-text-primary'
  }`;
}
