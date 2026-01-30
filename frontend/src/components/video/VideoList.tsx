import type { Video } from '../../types';
import { VideoCard } from './VideoCard';
import { ViewMode } from '../common/ViewModeToggle';
import { PlayIcon } from '@heroicons/react/24/outline';

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
      <div className="bg-bg-secondary rounded-xl p-12 text-center border border-border">
        <div className="w-16 h-16 bg-bg-tertiary rounded-full flex items-center justify-center mx-auto mb-4">
          <PlayIcon className="w-8 h-8 text-text-tertiary" />
        </div>
        <h3 className="text-lg font-semibold text-text-primary">No videos found</h3>
        <p className="mt-1 text-sm text-text-secondary">
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
