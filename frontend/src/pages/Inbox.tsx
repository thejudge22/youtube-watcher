import { useState, useMemo } from 'react';
import { 
  InboxIcon, 
  ArrowPathIcon, 
  SparklesIcon,
  FolderArrowDownIcon,
  TrashIcon
} from '@heroicons/react/24/outline';
import { useInboxVideos, useSaveVideo, useDiscardVideo, useBulkSaveVideos, useBulkDiscardVideos, useDetectShortsBatch } from '../hooks/useVideos';
import { useRefreshAllChannels } from '../hooks/useChannels';
import { useLocalStorage } from '../hooks/useLocalStorage';
import { VideoList } from '../components/video/VideoList';
import { Button } from '../components/common/Button';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { ChannelVideoGroup } from '../components/video/ChannelVideoGroup';
import { InboxViewToggle, type InboxViewMode } from '../components/inbox/InboxViewToggle';
import { ShortsFilterToggle } from '../components/inbox/ShortsFilterToggle';
import type { Video, ShortsFilter } from '../types';

export function Inbox() {
  const [viewMode, setViewMode] = useLocalStorage<InboxViewMode>('inbox-view-mode', 'grouped');
  const [shortsFilter, setShortsFilter] = useLocalStorage<ShortsFilter>('inbox-shorts-filter', 'all');

  const { data: videos, isLoading, error, refetch } = useInboxVideos(undefined, shortsFilter);
  const saveVideo = useSaveVideo();
  const discardVideo = useDiscardVideo();
  const bulkSave = useBulkSaveVideos();
  const bulkDiscard = useBulkDiscardVideos();
  const refreshAll = useRefreshAllChannels();
  const detectShortsBatch = useDetectShortsBatch();

  const [bulkActionChannelId, setBulkActionChannelId] = useState<string | null>(null);
  const [bulkActionType, setBulkActionType] = useState<'save' | 'discard' | null>(null);

  const groupedVideos = useMemo(() => {
    if (!videos) return [];

    const groups = new Map<string, { channelName: string; channelId: string; videos: Video[] }>();

    for (const video of videos) {
      const channelId = video.channel_id || 'unknown';
      const existing = groups.get(channelId);

      if (existing) {
        existing.videos.push(video);
      } else {
        groups.set(channelId, {
          channelId,
          channelName: video.channel_name || 'Unknown Channel',
          videos: [video],
        });
      }
    }

    return Array.from(groups.values()).sort((a, b) =>
      a.channelName.localeCompare(b.channelName, undefined, { sensitivity: 'base' })
    );
  }, [videos]);

  const handleSave = (id: string) => {
    saveVideo.mutate(id);
  };

  const handleDiscard = (id: string) => {
    discardVideo.mutate(id);
  };

  const handleSaveAll = () => {
    if (videos && videos.length > 0) {
      const videoIds = videos.map((v) => v.id);
      bulkSave.mutate(videoIds);
    }
  };

  const handleDiscardAll = () => {
    if (videos && videos.length > 0) {
      const videoIds = videos.map((v) => v.id);
      bulkDiscard.mutate(videoIds);
    }
  };

  const handleChannelSaveAll = async (channelId: string, videoIds: string[]) => {
    setBulkActionChannelId(channelId);
    setBulkActionType('save');
    try {
      await bulkSave.mutateAsync(videoIds);
    } finally {
      setBulkActionChannelId(null);
      setBulkActionType(null);
    }
  };

  const handleChannelDiscardAll = async (channelId: string, videoIds: string[]) => {
    setBulkActionChannelId(channelId);
    setBulkActionType('discard');
    try {
      await bulkDiscard.mutateAsync(videoIds);
    } finally {
      setBulkActionChannelId(null);
      setBulkActionType(null);
    }
  };

  const handleRefresh = () => {
    refreshAll.mutate(undefined, {
      onSuccess: () => {
        refetch();
      },
    });
  };

  const handleDetectShorts = () => {
    detectShortsBatch.mutate(undefined, {
      onSuccess: () => {
        refetch();
      },
    });
  };

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
        <LoadingSpinner size="lg" />
        <p className="text-text-secondary text-sm animate-pulse">Loading your inbox...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-accent-red/10 border border-accent-red/30 rounded-xl p-6 text-center animate-scale-in">
          <div className="w-12 h-12 bg-accent-red/20 rounded-full flex items-center justify-center mx-auto mb-3">
            <InboxIcon className="w-6 h-6 text-accent-red" />
          </div>
          <p className="text-accent-red font-medium">Error loading videos</p>
          <p className="text-text-secondary text-sm mt-1">Please try again</p>
          <Button
            variant="secondary"
            onClick={() => refetch()}
            className="mt-4"
          >
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-blue to-accent-purple flex items-center justify-center shadow-glow-blue">
            <InboxIcon className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-text-primary">Inbox</h1>
            {videos && videos.length > 0 && (
              <p className="text-text-secondary text-sm">
                {videos.length} video{videos.length !== 1 ? 's' : ''} to review
                {shortsFilter !== 'all' && (
                  <span className="ml-2 text-text-tertiary">
                    ({shortsFilter === 'shorts' ? 'Shorts only' : 'Videos only'})
                  </span>
                )}
              </p>
            )}
          </div>
        </div>
        
        {/* Actions */}
        <div className="flex flex-wrap gap-2 items-center">
          <ShortsFilterToggle value={shortsFilter} onChange={setShortsFilter} />
          <div className="w-px h-6 bg-border mx-1" />
          <InboxViewToggle viewMode={viewMode} onChange={setViewMode} />
          <Button
            variant="secondary"
            onClick={handleDetectShorts}
            isLoading={detectShortsBatch.isPending}
            title="Detect which videos are Shorts"
            size="sm"
          >
            <SparklesIcon className="w-4 h-4 mr-1.5" />
            Detect Shorts
          </Button>
          <Button
            variant="secondary"
            onClick={handleRefresh}
            isLoading={refreshAll.isPending}
            size="sm"
          >
            <ArrowPathIcon className={`w-4 h-4 mr-1.5 ${refreshAll.isPending ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          {videos && videos.length > 0 && (
            <>
              <div className="w-px h-6 bg-border mx-1" />
              <Button
                variant="primary"
                onClick={handleSaveAll}
                isLoading={bulkSave.isPending}
                size="sm"
              >
                <FolderArrowDownIcon className="w-4 h-4 mr-1.5" />
                Save All
              </Button>
              <Button
                variant="danger"
                onClick={handleDiscardAll}
                isLoading={bulkDiscard.isPending}
                size="sm"
              >
                <TrashIcon className="w-4 h-4 mr-1.5" />
                Discard All
              </Button>
            </>
          )}
        </div>
      </div>

      {/* Empty State */}
      {videos?.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center animate-scale-in">
          <div className="w-20 h-20 rounded-2xl bg-bg-secondary flex items-center justify-center mb-4">
            <InboxIcon className="w-10 h-10 text-text-tertiary" />
          </div>
          <h3 className="text-lg font-semibold text-text-primary mb-1">Your inbox is empty</h3>
          <p className="text-text-secondary text-sm max-w-sm">
            Add some YouTube channels to start receiving video updates. Videos will appear here when they're published.
          </p>
        </div>
      )}

      {/* Content */}
      {videos && videos.length > 0 && (
        viewMode === 'flat' ? (
          <div className="animate-slide-up">
            <VideoList
              videos={videos || []}
              onSave={handleSave}
              onDiscard={handleDiscard}
              emptyMessage="No videos in inbox. Add channels to start receiving video updates."
            />
          </div>
        ) : (
          <div className="space-y-4 animate-slide-up">
            {groupedVideos.length > 0 ? (
              groupedVideos.map(group => (
                <ChannelVideoGroup
                  key={group.channelId}
                  channelId={group.channelId}
                  channelName={group.channelName}
                  videos={group.videos}
                  onSave={handleSave}
                  onDiscard={handleDiscard}
                  onSaveAll={(ids) => handleChannelSaveAll(group.channelId, ids)}
                  onDiscardAll={(ids) => handleChannelDiscardAll(group.channelId, ids)}
                  isSavingAll={bulkActionChannelId === group.channelId && bulkActionType === 'save'}
                  isDiscardingAll={bulkActionChannelId === group.channelId && bulkActionType === 'discard'}
                />
              ))
            ) : (
              <VideoList
                videos={[]}
                onSave={handleSave}
                onDiscard={handleDiscard}
                emptyMessage="No videos in inbox. Add channels to start receiving video updates."
              />
            )}
          </div>
        )
      )}
    </div>
  );
}
