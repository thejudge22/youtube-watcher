import { useState, useMemo } from 'react';
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
  const detectShortsBatch = useDetectShortsBatch();  // Issue #8: Shorts detection

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

    // Sort alphabetically by channel name (case-insensitive) for stable ordering
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

  // Issue #8: Handle Shorts detection
  const handleDetectShorts = () => {
    detectShortsBatch.mutate(undefined, {
      onSuccess: () => {
        refetch();
      },
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-900/50 border border-red-700 rounded-lg p-4 text-center">
          <p className="text-red-400">Error loading videos. Please try again.</p>
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
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Inbox</h1>
          {videos && videos.length > 0 && (
            <p className="text-gray-400 text-sm mt-1">
              {videos.length} video{videos.length !== 1 ? 's' : ''} to review
              {shortsFilter !== 'all' && (
                <span className="ml-2">
                  ({shortsFilter === 'shorts' ? 'Shorts only' : 'Videos only'})
                </span>
              )}
            </p>
          )}
        </div>
        <div className="flex space-x-3 items-center">
          {/* Issue #8: Shorts filter toggle */}
          <ShortsFilterToggle value={shortsFilter} onChange={setShortsFilter} />
          <InboxViewToggle viewMode={viewMode} onChange={setViewMode} />
          <Button
            variant="secondary"
            onClick={handleDetectShorts}
            isLoading={detectShortsBatch.isPending}
            title="Detect which videos are Shorts"
          >
            Detect Shorts
          </Button>
          <Button
            variant="secondary"
            onClick={handleRefresh}
            isLoading={refreshAll.isPending}
          >
            Refresh
          </Button>
          {videos && videos.length > 0 && (
            <>
              <Button
                variant="primary"
                onClick={handleSaveAll}
                isLoading={bulkSave.isPending}
              >
                Save All
              </Button>
              <Button
                variant="danger"
                onClick={handleDiscardAll}
                isLoading={bulkDiscard.isPending}
              >
                Discard All
              </Button>
            </>
          )}
        </div>
      </div>

      {viewMode === 'flat' ? (
        <VideoList
          videos={videos || []}
          onSave={handleSave}
          onDiscard={handleDiscard}
          emptyMessage="No videos in inbox. Add channels to start receiving video updates."
        />
      ) : (
        <div className="space-y-4">
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
      )}
    </div>
  );
}