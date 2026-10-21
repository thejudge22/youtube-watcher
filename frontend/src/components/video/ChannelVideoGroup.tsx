import { useState } from 'react';
import type { Video } from '../../types';
import { VideoList } from './VideoList';
import { ChevronRightIcon } from '@heroicons/react/24/outline';
import { Button } from '../common/Button';

interface ChannelVideoGroupProps {
  channelName: string;
  channelId: string;
  videos: Video[];
  onSave: (videoId: string) => void;
  onDiscard: (videoId: string) => void;
  onSaveAll: (videoIds: string[]) => void;
  onDiscardAll: (videoIds: string[]) => void;
  isSavingAll?: boolean;
  isDiscardingAll?: boolean;
  defaultExpanded?: boolean;
}

export function ChannelVideoGroup({
  channelName,
  videos,
  onSave,
  onDiscard,
  onSaveAll,
  onDiscardAll,
  isSavingAll = false,
  isDiscardingAll = false,
  defaultExpanded = true,
}: ChannelVideoGroupProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  const videoIds = videos.map(v => v.id);

  return (
    <div className="border border-border rounded-xl overflow-hidden bg-bg-secondary">
      {/* Header: the toggle and the bulk actions are siblings, not nested buttons */}
      <div className="flex flex-wrap items-center justify-between gap-2 px-4 py-3 hover:bg-bg-tertiary/50 transition-colors">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center gap-3 min-w-0 flex-1 basis-48 text-left"
          aria-expanded={isExpanded}
        >
          <ChevronRightIcon
            className={`w-4 h-4 flex-shrink-0 text-text-tertiary transition-transform ${isExpanded ? 'rotate-90' : ''}`}
          />
          <span className="font-medium text-text-primary truncate">{channelName}</span>
          <span className="flex-shrink-0 text-xs font-medium text-text-secondary bg-bg-tertiary px-2 py-0.5 rounded-full tabular-nums">
            {videos.length}
          </span>
        </button>

        {/* Per-channel bulk actions */}
        <div className="flex gap-2">
          <Button
            variant="primary"
            size="sm"
            onClick={() => onSaveAll(videoIds)}
            disabled={isSavingAll || isDiscardingAll}
            isLoading={isSavingAll}
          >
            Save All
          </Button>
          <Button
            variant="danger"
            size="sm"
            onClick={() => onDiscardAll(videoIds)}
            disabled={isSavingAll || isDiscardingAll}
            isLoading={isDiscardingAll}
          >
            Discard All
          </Button>
        </div>
      </div>

      {/* Video list */}
      {isExpanded && (
        <div className="p-4 bg-bg-primary border-t border-border">
          <VideoList
            videos={videos}
            onSave={onSave}
            onDiscard={onDiscard}
            showSaveButton={true}
            showDiscardButton={true}
          />
        </div>
      )}
    </div>
  );
}
