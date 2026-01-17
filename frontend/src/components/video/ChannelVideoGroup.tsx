import { useState } from 'react';
import { ChevronDownIcon, ChevronRightIcon } from '@heroicons/react/24/outline';
import type { Video } from '../../types';
import { VideoList } from './VideoList';
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
  channelId,
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
    <div className="border border-gray-700 rounded-lg overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 bg-gray-800 hover:bg-gray-750 transition-colors"
      >
        <div className="flex items-center gap-3">
          {isExpanded ? (
            <ChevronDownIcon className="w-5 h-5 text-gray-400" />
          ) : (
            <ChevronRightIcon className="w-5 h-5 text-gray-400" />
          )}
          <span className="font-medium text-white">{channelName}</span>
          <span className="text-sm text-gray-400">({videos.length} video{videos.length !== 1 ? 's' : ''})</span>
        </div>

        {/* Per-channel bulk actions */}
        <div className="flex gap-2" onClick={e => e.stopPropagation()}>
          <Button
            variant="primary"
            onClick={() => onSaveAll(videoIds)}
            disabled={isSavingAll || isDiscardingAll}
            isLoading={isSavingAll}
            className="px-2 py-1 text-sm"
          >
            Save All
          </Button>
          <Button
            variant="secondary"
            onClick={() => onDiscardAll(videoIds)}
            disabled={isSavingAll || isDiscardingAll}
            isLoading={isDiscardingAll}
            className="px-2 py-1 text-sm"
          >
            Discard All
          </Button>
        </div>
      </button>

      {/* Video list */}
      {isExpanded && (
        <div className="p-4 bg-gray-900">
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
