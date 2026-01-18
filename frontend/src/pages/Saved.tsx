import React, { useState, useMemo } from 'react';
import { useSavedVideos, useDiscardVideo } from '../hooks/useVideos';
import { useChannels } from '../hooks/useChannels';
import { VideoList } from '../components/video/VideoList';
import { RecentlyDeletedModal } from '../components/video/RecentlyDeletedModal';
import { Button } from '../components/common/Button';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import ViewModeToggle, { ViewMode } from '../components/common/ViewModeToggle';
import { useLocalStorage } from '../hooks/useLocalStorage';
import type { SavedVideosParams } from '../types';

type SortBy = 'published_at' | 'saved_at';
type Order = 'asc' | 'desc';

const SORT_OPTIONS: { label: string; value: SortBy; order: Order }[] = [
  { label: 'Published Date (Newest)', value: 'published_at', order: 'desc' },
  { label: 'Published Date (Oldest)', value: 'published_at', order: 'asc' },
  { label: 'Saved Date (Newest)', value: 'saved_at', order: 'desc' },
  { label: 'Saved Date (Oldest)', value: 'saved_at', order: 'asc' },
];

export function Saved() {
  const [channelId, setChannelId] = useState<string>('');
  const [sortBy, setSortBy] = useState<SortBy>('published_at');
  const [order, setOrder] = useState<Order>('desc');
  const [showRecentlyDeleted, setShowRecentlyDeleted] = useState(false);
  const [viewMode, setViewMode] = useLocalStorage<ViewMode>('saved-view-mode', 'large');

  const params: SavedVideosParams = useMemo(() => {
    const p: SavedVideosParams = {};
    if (channelId) {
      p.channel_id = channelId;
    }
    if (sortBy) {
      p.sort_by = sortBy;
    }
    if (order) {
      p.order = order;
    }
    return p;
  }, [channelId, sortBy, order]);

  const { data: videos, isLoading, error, refetch } = useSavedVideos(params);
  const { data: channels } = useChannels();
  const discardVideo = useDiscardVideo();

  const handleDiscard = (id: string) => {
    discardVideo.mutate(id);
  };

  const handleSortChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selected = SORT_OPTIONS.find((opt) => opt.label === e.target.value);
    if (selected) {
      setSortBy(selected.value);
      setOrder(selected.order);
    }
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
          <p className="text-red-400">Error loading saved videos. Please try again.</p>
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
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between mb-6 gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Saved Videos</h1>
          {videos && videos.length > 0 && (
            <p className="text-gray-400 text-sm mt-1">
              {videos.length} video{videos.length !== 1 ? 's' : ''} saved
            </p>
          )}
        </div>
        <div className="flex flex-wrap gap-3">
          <Button
            variant="secondary"
            onClick={() => setShowRecentlyDeleted(true)}
          >
            Recently Deleted
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-gray-800 rounded-lg p-4 mb-6">
        <div className="flex flex-wrap gap-4 items-end">
          {/* Channel Filter */}
          <div className="flex-1 min-w-[200px]">
            <label htmlFor="channel-filter" className="block text-sm font-medium text-gray-300 mb-1">
              Filter by Channel
            </label>
            <select
              id="channel-filter"
              value={channelId}
              onChange={(e) => setChannelId(e.target.value)}
              className="w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Channels</option>
              {channels?.map((channel) => (
                <option key={channel.id} value={channel.id}>
                  {channel.name}
                </option>
              ))}
            </select>
          </div>

          {/* Sort Filter */}
          <div className="flex-1 min-w-[200px]">
            <label htmlFor="sort-filter" className="block text-sm font-medium text-gray-300 mb-1">
              Sort By
            </label>
            <select
              id="sort-filter"
              value={SORT_OPTIONS.find((opt) => opt.value === sortBy && opt.order === order)?.label || ''}
              onChange={handleSortChange}
              className="w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {SORT_OPTIONS.map((option) => (
                <option key={option.label} value={option.label}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* View Mode Toggle */}
          <div>
            <ViewModeToggle viewMode={viewMode} onChange={setViewMode} />
          </div>
        </div>
      </div>

      <VideoList
        videos={videos || []}
        onDiscard={handleDiscard}
        showSaveButton={false}
        emptyMessage="No saved videos. Save videos from the inbox to watch later."
        viewMode={viewMode}
      />

      <RecentlyDeletedModal
        isOpen={showRecentlyDeleted}
        onClose={() => setShowRecentlyDeleted(false)}
      />
    </div>
  );
}