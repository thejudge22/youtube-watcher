import type { Video } from '../../types';
import { VideoCard } from './VideoCard';
import { ViewMode } from '../common/ViewModeToggle';

interface VideoListProps {
  videos: Video[];
  onSave?: (id: string) => void;
  onDiscard: (id: string) => void;
  emptyMessage?: string;
  showSaveButton?: boolean;
  showDiscardButton?: boolean;
  viewMode?: ViewMode;
  isSelectionMode?: boolean;
  selectedIds?: Set<string>;
  onToggleSelect?: (id: string, shiftKey: boolean) => void;
  // Touch drag selection props
  containerRef?: React.RefObject<HTMLDivElement>;
  getItemTouchProps?: (id: string) => object;
  getSelectZoneProps?: (id: string) => object;
  previewRange?: Set<string>;
  dragStartId?: string | null;
  dragEndId?: string | null;
}

export function VideoList({
  videos,
  onSave,
  onDiscard,
  emptyMessage,
  showSaveButton = true,
  showDiscardButton = true,
  viewMode = 'large',
  isSelectionMode = false,
  selectedIds = new Set(),
  onToggleSelect,
  containerRef,
  getItemTouchProps,
  getSelectZoneProps,
  previewRange = new Set(),
  dragStartId,
  dragEndId,
}: VideoListProps) {
  if (videos.length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg p-12 text-center">
        <svg
          className="mx-auto h-12 w-12 text-gray-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
          />
        </svg>
        <h3 className="mt-2 text-lg font-medium text-white">No videos found</h3>
        <p className="mt-1 text-sm text-gray-400">
          {emptyMessage || 'No videos to display.'}
        </p>
      </div>
    );
  }

  const containerClasses = {
    large: 'grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 items-stretch',
    compact: 'grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6 gap-4 items-stretch',
    list: 'flex flex-col gap-2',
  };

  return (
    <div ref={containerRef} className={containerClasses[viewMode]}>
      {videos.map((video) => {
        const touchProps = getItemTouchProps?.(video.id) || {};
        const selectZoneProps = getSelectZoneProps?.(video.id) || {};
        const isInPreviewRange = previewRange.has(video.id);
        const isDragStart = dragStartId === video.id;
        const isDragEnd = dragEndId === video.id;

        return (
          <VideoCard
            key={video.id}
            video={video}
            onSave={onSave}
            onDiscard={onDiscard}
            showSaveButton={showSaveButton}
            showDiscardButton={showDiscardButton}
            viewMode={viewMode}
            isSelectionMode={isSelectionMode}
            isSelected={selectedIds.has(video.id)}
            onToggleSelect={onToggleSelect}
            touchProps={touchProps}
            selectZoneProps={selectZoneProps}
            isInPreviewRange={isInPreviewRange}
            isDragStart={isDragStart}
            isDragEnd={isDragEnd}
          />
        );
      })}
    </div>
  );
}