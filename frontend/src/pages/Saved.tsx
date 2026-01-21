import React, { useState, useMemo } from 'react';
import { PlayIcon, ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';
import { useSavedVideos, useDiscardVideo, useBulkDiscardVideos, useSavedVideoChannels } from '../hooks/useVideos';
import { VideoList } from '../components/video/VideoList';
import { RecentlyDeletedModal } from '../components/video/RecentlyDeletedModal';
import { Button } from '../components/common/Button';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import ViewModeToggle, { ViewMode } from '../components/common/ViewModeToggle';
import { useLocalStorage } from '../hooks/useLocalStorage';
import { openPlaylist } from '../utils/playlist';
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
  const [channelYoutubeId, setChannelYoutubeId] = useState<string>('');
  const [sortBy, setSortBy] = useState<SortBy>('published_at');
  const [order, setOrder] = useState<Order>('desc');
  const [showRecentlyDeleted, setShowRecentlyDeleted] = useState(false);
  const [viewMode, setViewMode] = useLocalStorage<ViewMode>('saved-view-mode', 'large');
  const [isSelectionMode, setIsSelectionMode] = useState(false);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [currentPage, setCurrentPage] = useState(1);

  const params: SavedVideosParams = useMemo(() => {
    const p: SavedVideosParams = {};
    if (channelYoutubeId) {
      p.channel_youtube_id = channelYoutubeId;
    }
    if (sortBy) {
      p.sort_by = sortBy;
    }
    if (order) {
      p.order = order;
    }
    p.limit = 100;
    p.offset = (currentPage - 1) * 100;
    return p;
  }, [channelYoutubeId, sortBy, order, currentPage]);

  // Reset to page 1 when filters change
  const handleFilterChange = () => {
    setCurrentPage(1);
  };

  const { data, isLoading, error, refetch } = useSavedVideos(params);
  const { data: channelOptions } = useSavedVideoChannels();
  const discardVideo = useDiscardVideo();
  const bulkDiscard = useBulkDiscardVideos();

  const handleDiscard = (id: string) => {
    discardVideo.mutate(id);
  };

  const handleToggleSelect = (id: string) => {
    setSelectedIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(id)) {
        newSet.delete(id);
      } else {
        newSet.add(id);
      }
      return newSet;
    });
  };

  const handleSelectAll = () => {
    setSelectedIds(new Set(videos?.map(v => v.id) || []));
  };

  const handleDeselectAll = () => {
    setSelectedIds(new Set());
  };

  const handleRemoveSelected = () => {
    const ids = Array.from(selectedIds);
    bulkDiscard.mutate(ids, {
      onSuccess: () => {
        setSelectedIds(new Set());
        setIsSelectionMode(false);
      }
    });
  };

  const handleToggleSelectionMode = () => {
    setIsSelectionMode(!isSelectionMode);
    setSelectedIds(new Set()); // Clear selections when toggling mode
  };

  const handlePlayAsPlaylist = () => {
    if (!videos) return;

    const selectedVideos = videos.filter(v => selectedIds.has(v.id));
    const result = openPlaylist(selectedVideos);

    if (result.truncated) {
      console.log(`Playlist opened with ${result.videoCount} videos (some were truncated due to 50 video limit)`);
    }

    // Exit selection mode after playing
    setIsSelectionMode(false);
    setSelectedIds(new Set());
  };

  const handleSortChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    const selected = SORT_OPTIONS.find((opt) => opt.label === e.target.value);
    if (selected) {
      setSortBy(selected.value);
      setOrder(selected.order);
      handleFilterChange();
    }
  };

  const handleChannelChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    setChannelYoutubeId(e.target.value);
    handleFilterChange();
  };

  const videos = data?.videos ?? [];
  const totalCount = data?.total ?? 0;
  const totalPages = Math.ceil(totalCount / 100);

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
      <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between mb-6 gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">Saved Videos</h1>
          {totalCount > 0 && (
            <p className="text-gray-400 text-sm mt-1">
              {totalCount} video{totalCount !== 1 ? 's' : ''} saved
            </p>
          )}
        </div>
        <div className="flex flex-wrap gap-3 sm:flex-nowrap">
          <Button
            variant={isSelectionMode ? "primary" : "secondary"}
            onClick={handleToggleSelectionMode}
          >
            {isSelectionMode ? 'Cancel Selection' : 'Select Videos'}
          </Button>
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
              value={channelYoutubeId}
              onChange={handleChannelChange}
              className="w-full bg-gray-700 border border-gray-600 text-white rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">All Channels</option>
              {channelOptions?.map((option) => (
                <option key={option.channel_youtube_id} value={option.channel_youtube_id}>
                  {option.channel_name} ({option.video_count})
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
            <label htmlFor="view-mode-toggle" className="block text-sm font-medium text-gray-300 mb-1">
              View Mode
            </label>
            <ViewModeToggle viewMode={viewMode} onChange={setViewMode} />
          </div>
        </div>
      </div>

      {/* Selection Toolbar - shown when in selection mode */}
      {isSelectionMode && (
        <div className="bg-gray-800 rounded-lg p-4 mb-4 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-4">
            <span className="text-gray-300">
              {selectedIds.size} video{selectedIds.size !== 1 ? 's' : ''} selected
            </span>
            <Button variant="secondary" onClick={handleSelectAll} className="px-3 py-1.5 text-sm">
              Select All
            </Button>
            <Button variant="secondary" onClick={handleDeselectAll} className="px-3 py-1.5 text-sm">
              Deselect All
            </Button>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="primary"
              onClick={handlePlayAsPlaylist}
              disabled={selectedIds.size === 0}
            >
              <PlayIcon className="w-4 h-4 mr-2" />
              Play as Playlist
            </Button>
            <Button
              variant="danger"
              onClick={handleRemoveSelected}
              disabled={selectedIds.size === 0}
            >
              Remove Selected ({selectedIds.size})
            </Button>
          </div>
        </div>
      )}

      <VideoList
        videos={videos}
        onDiscard={handleDiscard}
        showSaveButton={false}
        showDiscardButton={false}
        emptyMessage="No saved videos. Save videos from the inbox to watch later."
        viewMode={viewMode}
        isSelectionMode={isSelectionMode}
        selectedIds={selectedIds}
        onToggleSelect={handleToggleSelect}
      />

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="mt-6 flex items-center justify-center gap-2">
          <Button
            variant="secondary"
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            className="px-3 py-2"
          >
            <ChevronLeftIcon className="w-5 h-5" />
          </Button>

          <div className="flex items-center gap-1">
            {Array.from({ length: Math.min(totalPages, 10) }, (_, i) => {
              // Show first page, last page, current page, and pages around current
              let pageNum: number;
              if (totalPages <= 10) {
                pageNum = i + 1;
              } else if (currentPage <= 5) {
                pageNum = i < 7 ? i + 1 : (i === 7 ? -1 : totalPages);
              } else if (currentPage >= totalPages - 4) {
                pageNum = i < 2 ? i + 1 : (i === 2 ? -1 : totalPages - 6 + i);
              } else {
                pageNum = i < 2 ? i + 1 : (i === 2 ? -1 : (i === 7 ? -1 : currentPage - 3 + i));
              }

              if (pageNum === -1) {
                return <span key={i} className="px-2 text-gray-500">...</span>;
              }

              return (
                <button
                  key={i}
                  onClick={() => setCurrentPage(pageNum)}
                  className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                    currentPage === pageNum
                      ? 'bg-blue-600 text-white'
                      : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
                  }`}
                >
                  {pageNum}
                </button>
              );
            })}
          </div>

          <Button
            variant="secondary"
            onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
            disabled={currentPage === totalPages}
            className="px-3 py-2"
          >
            <ChevronRightIcon className="w-5 h-5" />
          </Button>
        </div>
      )}

      <RecentlyDeletedModal
        isOpen={showRecentlyDeleted}
        onClose={() => setShowRecentlyDeleted(false)}
      />
    </div>
  );
}