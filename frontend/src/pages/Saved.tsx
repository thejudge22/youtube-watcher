import React, { useState, useMemo } from 'react';
import { 
  BookmarkIcon, 
  PlayIcon, 
  ChevronLeftIcon, 
  ChevronRightIcon,
  ClockIcon,
  FunnelIcon,
  ArrowPathIcon,
  CheckCircleIcon,
  XCircleIcon
} from '@heroicons/react/24/outline';
import { useSavedVideos, useDiscardVideo, useBulkDiscardVideos, useSavedVideoChannels } from '../hooks/useVideos';
import { useTouchDragSelect } from '../hooks/useTouchDragSelect';
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
  const [lastClickedId, setLastClickedId] = useState<string | null>(null);
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

  const handleFilterChange = () => {
    setCurrentPage(1);
    setLastClickedId(null);
  };

  const { data, isLoading, error, refetch } = useSavedVideos(params);
  const { data: channelOptions } = useSavedVideoChannels();
  const discardVideo = useDiscardVideo();
  const bulkDiscard = useBulkDiscardVideos();

  const handleDiscard = (id: string) => {
    discardVideo.mutate(id);
  };

  const handleToggleSelect = (id: string, shiftKey: boolean = false) => {
    setSelectedIds(prev => {
      const newSet = new Set(prev);

      if (shiftKey && lastClickedId) {
        const lastIndex = videos.findIndex(v => v.id === lastClickedId);
        const currentIndex = videos.findIndex(v => v.id === id);

        if (lastIndex !== -1 && currentIndex !== -1) {
          const start = Math.min(lastIndex, currentIndex);
          const end = Math.max(lastIndex, currentIndex);

          for (let i = start; i <= end; i++) {
            newSet.add(videos[i].id);
          }
        } else {
          if (newSet.has(id)) {
            newSet.delete(id);
          } else {
            newSet.add(id);
          }
        }
      } else {
        if (newSet.has(id)) {
          newSet.delete(id);
        } else {
          newSet.add(id);
        }
      }

      return newSet;
    });

    setLastClickedId(id);
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
    setSelectedIds(new Set());
    setLastClickedId(null);
  };

  const handlePlayAsPlaylist = () => {
    if (!videos) return;

    const selectedVideos = videos.filter(v => selectedIds.has(v.id));
    const result = openPlaylist(selectedVideos);

    if (result.truncated) {
      console.log(`Playlist opened with ${result.videoCount} videos (some were truncated due to 50 video limit)`);
    }
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

  const touchDragSelect = useTouchDragSelect({
    isEnabled: isSelectionMode,
    items: videos.map(v => ({ id: v.id })),
    selectedIds,
    lastClickedId,
    onSelectionChange: (newSelectedIds, newLastClickedId) => {
      setSelectedIds(newSelectedIds);
      setLastClickedId(newLastClickedId);
    },
  });

  if (isLoading) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] gap-4">
        <LoadingSpinner size="lg" />
        <p className="text-text-secondary text-sm animate-pulse">Loading your saved videos...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-accent-red/10 border border-accent-red/30 rounded-xl p-6 text-center animate-scale-in">
          <div className="w-12 h-12 bg-accent-red/20 rounded-full flex items-center justify-center mx-auto mb-3">
            <BookmarkIcon className="w-6 h-6 text-accent-red" />
          </div>
          <p className="text-accent-red font-medium">Error loading saved videos</p>
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
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-green to-accent-blue flex items-center justify-center shadow-glow-green">
            <BookmarkIcon className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-text-primary">Saved Videos</h1>
            {totalCount > 0 && (
              <p className="text-text-secondary text-sm">
                {totalCount} video{totalCount !== 1 ? 's' : ''} saved
              </p>
            )}
          </div>
        </div>
        <div className="flex flex-wrap gap-2 items-center">
          <Button
            variant={isSelectionMode ? "primary" : "secondary"}
            onClick={handleToggleSelectionMode}
            size="sm"
          >
            {isSelectionMode ? 'Cancel Selection' : 'Select Videos'}
          </Button>
          <Button
            variant="secondary"
            onClick={() => setShowRecentlyDeleted(true)}
            size="sm"
          >
            <ClockIcon className="w-4 h-4 mr-1.5" />
            Recently Deleted
          </Button>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-bg-secondary rounded-xl p-4 mb-6 border border-border animate-slide-up">
        <div className="flex flex-wrap gap-4 items-end">
          {/* Channel Filter */}
          <div className="flex-1 min-w-[200px]">
            <label htmlFor="channel-filter" className="block text-sm font-medium text-text-secondary mb-1.5">
              <FunnelIcon className="w-4 h-4 inline-block mr-1.5 -mt-0.5" />
              Filter by Channel
            </label>
            <select
              id="channel-filter"
              value={channelYoutubeId}
              onChange={handleChannelChange}
              className="w-full bg-bg-tertiary border border-border text-text-primary rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent-blue focus:border-transparent transition-all"
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
            <label htmlFor="sort-filter" className="block text-sm font-medium text-text-secondary mb-1.5">
              <ArrowPathIcon className="w-4 h-4 inline-block mr-1.5 -mt-0.5" />
              Sort By
            </label>
            <select
              id="sort-filter"
              value={SORT_OPTIONS.find((opt) => opt.value === sortBy && opt.order === order)?.label || ''}
              onChange={handleSortChange}
              className="w-full bg-bg-tertiary border border-border text-text-primary rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-accent-blue focus:border-transparent transition-all"
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
            <label htmlFor="view-mode-toggle" className="block text-sm font-medium text-text-secondary mb-1.5">
              View Mode
            </label>
            <ViewModeToggle viewMode={viewMode} onChange={setViewMode} />
          </div>
        </div>
      </div>

      {/* Selection Toolbar */}
      {isSelectionMode && (
        <div className="bg-bg-secondary rounded-xl p-4 mb-4 border border-accent-blue/30 flex flex-wrap items-center justify-between gap-4 animate-slide-up">
          <div className="flex items-center gap-4">
            <span className="text-text-primary font-medium">
              {selectedIds.size} video{selectedIds.size !== 1 ? 's' : ''} selected
            </span>
            <Button 
              variant="secondary" 
              onClick={handleSelectAll} 
              size="sm" 
              className="gap-1.5 bg-bg-tertiary hover:bg-accent-blue/20 hover:text-accent-blue hover:border-accent-blue/50 transition-all"
            >
              <CheckCircleIcon className="w-4 h-4" />
              Select All
            </Button>
            <Button 
              variant="secondary" 
              onClick={handleDeselectAll} 
              size="sm"
              disabled={selectedIds.size === 0}
              className="gap-1.5 bg-bg-tertiary hover:bg-accent-red/20 hover:text-accent-red hover:border-accent-red/50 transition-all disabled:opacity-40"
            >
              <XCircleIcon className="w-4 h-4" />
              Clear Selection
            </Button>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="primary"
              onClick={handlePlayAsPlaylist}
              disabled={selectedIds.size === 0}
              size="sm"
            >
              <PlayIcon className="w-4 h-4 mr-1.5" />
              Play as Playlist
            </Button>
            <Button
              variant="danger"
              onClick={handleRemoveSelected}
              disabled={selectedIds.size === 0}
              size="sm"
            >
              Remove Selected
            </Button>
          </div>
        </div>
      )}

      {/* Empty State */}
      {videos.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center animate-scale-in">
          <div className="w-20 h-20 rounded-2xl bg-bg-secondary flex items-center justify-center mb-4">
            <BookmarkIcon className="w-10 h-10 text-text-tertiary" />
          </div>
          <h3 className="text-lg font-semibold text-text-primary mb-1">No saved videos yet</h3>
          <p className="text-text-secondary text-sm max-w-sm">
            Videos you save from your inbox will appear here. Save videos to watch them later.
          </p>
        </div>
      )}

      {/* Video List */}
      {videos.length > 0 && (
        <div className="animate-slide-up">
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
            containerRef={touchDragSelect.containerRef}
            getItemTouchProps={touchDragSelect.getItemProps}
            getSelectZoneProps={touchDragSelect.getSelectZoneProps}
            previewRange={touchDragSelect.previewRange}
            dragStartId={touchDragSelect.dragStartId}
            dragEndId={touchDragSelect.dragEndId}
          />
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="mt-8 flex items-center justify-center gap-2 animate-slide-up">
          <Button
            variant="secondary"
            onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
            disabled={currentPage === 1}
            size="sm"
            className="px-3"
          >
            <ChevronLeftIcon className="w-5 h-5" />
          </Button>

          <div className="flex items-center gap-1">
            {Array.from({ length: Math.min(totalPages, 10) }, (_, i) => {
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
                return <span key={i} className="px-2 text-text-tertiary">...</span>;
              }

              return (
                <button
                  key={i}
                  onClick={() => setCurrentPage(pageNum)}
                  className={`px-3.5 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                    currentPage === pageNum
                      ? 'bg-accent-blue text-white shadow-glow-blue'
                      : 'bg-bg-secondary text-text-secondary hover:bg-bg-tertiary hover:text-text-primary'
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
            size="sm"
            className="px-3"
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
