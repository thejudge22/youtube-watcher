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
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 10h16M4 14h16M4 18h16" />
        </svg>
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
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
        </svg>
        <span>Grouped</span>
      </button>
    </div>
  );
}
