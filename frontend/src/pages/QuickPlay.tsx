import { useState } from 'react';
import {
  PlayIcon,
  FilmIcon,
  BoltIcon,
  ArrowPathIcon,
  TrashIcon,
  ExclamationTriangleIcon,
} from '@heroicons/react/24/outline';
import { useBulkDiscardVideos, useQuickPlayVideos } from '../hooks/useVideos';
import { Button } from '../components/common/Button';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { Modal } from '../components/common/Modal';
import { openPlaylist } from '../utils/playlist';
import type { Video } from '../types';

type QuickPlaySection = 'regular' | 'shorts';

interface RemovalTarget {
  section: QuickPlaySection;
  itemName: 'Video' | 'Short';
  videoIds: string[];
}

function formatDate(dateString: string) {
  const date = new Date(dateString);
  return date.toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function QuickPlayPanel({
  title,
  icon: Icon,
  videos,
  isLoading,
  emptyMessage,
  itemName,
  onRemove,
  isRemoving,
  isRemovalDisabled,
}: {
  title: string;
  icon: React.ElementType;
  videos: Video[];
  isLoading: boolean;
  emptyMessage: string;
  itemName: 'Video' | 'Short';
  onRemove: () => void;
  isRemoving: boolean;
  isRemovalDisabled: boolean;
}) {
  const itemLabel = `${itemName}${videos.length === 1 ? '' : 's'}`;

  return (
    <div className="bg-bg-secondary rounded-xl border border-border flex flex-col">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 px-4 py-3 border-b border-border">
        <div className="flex items-center gap-2">
          <Icon className="w-5 h-5 text-accent-blue" />
          <h2 className="font-semibold text-text-primary">{title}</h2>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-text-secondary bg-bg-tertiary px-2.5 py-1 rounded-full">
            {videos.length}
          </span>
          <Button
            variant="danger"
            size="sm"
            onClick={onRemove}
            disabled={isLoading || videos.length === 0 || isRemovalDisabled}
            isLoading={isRemoving}
          >
            {!isRemoving && <TrashIcon className="w-4 h-4 mr-1.5" />}
            Remove {videos.length} {itemLabel}
          </Button>
        </div>
      </div>

      <div className="flex-1 min-h-0 overflow-y-auto max-h-[calc(100vh-320px)] p-2">
        {isLoading ? (
          <div className="flex flex-col items-center justify-center py-12 gap-3">
            <LoadingSpinner size="md" />
            <span className="text-sm text-text-secondary">Loading...</span>
          </div>
        ) : videos.length === 0 ? (
          <div className="flex flex-col items-center justify-center py-12 text-center px-4">
            <FilmIcon className="w-8 h-8 text-text-tertiary mb-2" />
            <p className="text-sm text-text-secondary">{emptyMessage}</p>
          </div>
        ) : (
          <div className="flex flex-col gap-1">
            {videos.map((video) => (
              <a
                key={video.id}
                href={video.video_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex gap-3 p-2 rounded-lg hover:bg-bg-tertiary transition-colors group"
                title={video.title}
              >
                <img
                  src={video.thumbnail_url || ''}
                  alt=""
                  loading="lazy"
                  className="w-[120px] h-[68px] rounded-md object-cover flex-shrink-0 bg-bg-tertiary"
                  onError={(e) => {
                    (e.target as HTMLImageElement).style.display = 'none';
                  }}
                />
                <div className="flex flex-col justify-center min-w-0">
                  <span className="text-sm font-medium text-text-primary line-clamp-2 leading-snug group-hover:text-accent-blue transition-colors">
                    {video.title}
                  </span>
                  <span className="text-xs text-text-secondary mt-0.5 truncate">
                    {video.channel_name || 'Unknown Channel'}
                  </span>
                  <span className="text-xs text-text-tertiary">
                    {formatDate(video.published_at)}
                  </span>
                </div>
              </a>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export function QuickPlay() {
  const { regular, shorts } = useQuickPlayVideos();
  const bulkDiscard = useBulkDiscardVideos();
  const [removalTarget, setRemovalTarget] = useState<RemovalTarget | null>(null);
  const [isRemovalModalOpen, setIsRemovalModalOpen] = useState(false);
  const [removalError, setRemovalError] = useState<string | null>(null);

  const videos = regular.data ?? [];
  const shortVideos = shorts.data ?? [];
  const isLoading = regular.isLoading || shorts.isLoading;
  const error = regular.error || shorts.error;

  const handlePlayVideos = () => {
    if (!videos.length) return;
    openPlaylist(videos);
  };

  const handlePlayShorts = () => {
    if (!shortVideos.length) return;
    openPlaylist(shortVideos);
  };

  const handlePlayAll = () => {
    const all = [...videos, ...shortVideos];
    if (!all.length) return;
    openPlaylist(all);
  };

  const refetch = () => {
    regular.refetch();
    shorts.refetch();
  };

  const openRemovalModal = (
    section: QuickPlaySection,
    itemName: RemovalTarget['itemName'],
    sectionVideos: Video[],
  ) => {
    if (!sectionVideos.length || bulkDiscard.isPending) return;

    setRemovalTarget({
      section,
      itemName,
      videoIds: sectionVideos.map((video) => video.id),
    });
    setRemovalError(null);
    setIsRemovalModalOpen(true);
  };

  const closeRemovalModal = () => {
    if (bulkDiscard.isPending) return;
    setIsRemovalModalOpen(false);
    setRemovalTarget(null);
    setRemovalError(null);
  };

  const handleConfirmRemoval = async () => {
    if (!removalTarget || bulkDiscard.isPending) return;

    const target = removalTarget;
    setRemovalError(null);
    setIsRemovalModalOpen(false);

    try {
      await bulkDiscard.mutateAsync(target.videoIds);
      await (target.section === 'regular' ? regular.refetch() : shorts.refetch());
      setRemovalTarget(null);
    } catch {
      setRemovalError(
        `Unable to move the selected ${target.itemName.toLowerCase()}${target.videoIds.length === 1 ? '' : 's'} to Recently Deleted. Please try again.`,
      );
      setIsRemovalModalOpen(true);
    }
  };

  const removalItemLabel = removalTarget
    ? `${removalTarget.itemName}${removalTarget.videoIds.length === 1 ? '' : 's'}`
    : 'Videos';

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-accent-red/10 border border-accent-red/30 rounded-xl p-6 text-center animate-scale-in">
          <div className="w-12 h-12 bg-accent-red/20 rounded-full flex items-center justify-center mx-auto mb-3">
            <PlayIcon className="w-6 h-6 text-accent-red" />
          </div>
          <p className="text-accent-red font-medium">Error loading videos</p>
          <p className="text-text-secondary text-sm mt-1">Please try again</p>
          <Button variant="secondary" onClick={refetch} className="mt-4">
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
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-red to-accent-orange flex items-center justify-center shadow-glow">
            <PlayIcon className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-text-primary">QuickPlay</h1>
            {!isLoading && (
              <p className="text-text-secondary text-sm">
                {videos.length + shortVideos.length} video
                {videos.length + shortVideos.length !== 1 ? 's' : ''} ready to play
              </p>
            )}
          </div>
        </div>

        <div className="flex flex-wrap gap-2 items-center">
          <Button
            variant="secondary"
            onClick={refetch}
            isLoading={isLoading}
            size="sm"
          >
            <ArrowPathIcon className={`w-4 h-4 mr-1.5 ${isLoading ? 'animate-spin' : ''}`} />
            Refresh
          </Button>
          <div className="w-px h-6 bg-border mx-1" />
          <Button
            variant="primary"
            onClick={handlePlayVideos}
            disabled={!videos.length}
            size="sm"
          >
            <FilmIcon className="w-4 h-4 mr-1.5" />
            Play Videos
          </Button>
          <Button
            variant="primary"
            onClick={handlePlayShorts}
            disabled={!shortVideos.length}
            size="sm"
          >
            <BoltIcon className="w-4 h-4 mr-1.5" />
            Play Shorts
          </Button>
          <Button
            variant="success"
            onClick={handlePlayAll}
            disabled={!videos.length && !shortVideos.length}
            size="sm"
          >
            <PlayIcon className="w-4 h-4 mr-1.5" />
            Play All
          </Button>
        </div>
      </div>

      {/* Panels */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <QuickPlayPanel
          title="Oldest Videos"
          icon={FilmIcon}
          videos={videos}
          isLoading={regular.isLoading}
          emptyMessage="No saved videos found. Save videos from your inbox to see them here."
          itemName="Video"
          onRemove={() => openRemovalModal('regular', 'Video', videos)}
          isRemoving={bulkDiscard.isPending && removalTarget?.section === 'regular'}
          isRemovalDisabled={bulkDiscard.isPending}
        />
        <QuickPlayPanel
          title="Oldest Shorts"
          icon={BoltIcon}
          videos={shortVideos}
          isLoading={shorts.isLoading}
          emptyMessage="No saved shorts found. Save shorts from your inbox to see them here."
          itemName="Short"
          onRemove={() => openRemovalModal('shorts', 'Short', shortVideos)}
          isRemoving={bulkDiscard.isPending && removalTarget?.section === 'shorts'}
          isRemovalDisabled={bulkDiscard.isPending}
        />
      </div>

      <Modal
        isOpen={isRemovalModalOpen && removalTarget !== null}
        onClose={closeRemovalModal}
        title="Move to Recently Deleted?"
      >
        {removalTarget && (
          <div className="flex flex-col items-center text-center py-4">
            <div className="w-16 h-16 rounded-full bg-accent-red/10 flex items-center justify-center mb-4">
              <ExclamationTriangleIcon className="w-8 h-8 text-accent-red" />
            </div>
            <p className="text-text-primary font-medium mb-2">
              Remove {removalTarget.videoIds.length} {removalItemLabel} from Saved Videos?
            </p>
            <p className="text-text-secondary text-sm px-4">
              {removalTarget.videoIds.length === 1 ? 'It' : 'They'} will be moved to Recently Deleted, where {removalTarget.videoIds.length === 1 ? 'it' : 'they'} can be restored. If more {removalTarget.itemName.toLowerCase()}s are available, the next oldest batch will load here; otherwise, this section will be empty.
            </p>
            {removalError && (
              <p className="text-accent-red text-sm mt-4" role="alert">
                {removalError}
              </p>
            )}
            <div className="flex gap-3 mt-6 w-full">
              <Button
                variant="secondary"
                onClick={closeRemovalModal}
                className="flex-1"
                disabled={bulkDiscard.isPending}
              >
                Cancel
              </Button>
              <Button
                variant="danger"
                onClick={handleConfirmRemoval}
                className="flex-1"
                isLoading={bulkDiscard.isPending}
              >
                <TrashIcon className="w-4 h-4 mr-1.5" />
                Yes, Remove {removalTarget.videoIds.length}
              </Button>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
