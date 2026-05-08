import {
  PlayIcon,
  FilmIcon,
  BoltIcon,
  ArrowPathIcon,
} from '@heroicons/react/24/outline';
import { useQuickPlayVideos } from '../hooks/useVideos';
import { Button } from '../components/common/Button';
import { LoadingSpinner } from '../components/common/LoadingSpinner';
import { openPlaylist } from '../utils/playlist';
import type { Video } from '../types';

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
}: {
  title: string;
  icon: React.ElementType;
  videos: Video[];
  isLoading: boolean;
  emptyMessage: string;
}) {
  return (
    <div className="bg-bg-secondary rounded-xl border border-border flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div className="flex items-center gap-2">
          <Icon className="w-5 h-5 text-accent-blue" />
          <h2 className="font-semibold text-text-primary">{title}</h2>
        </div>
        <span className="text-xs font-medium text-text-secondary bg-bg-tertiary px-2.5 py-1 rounded-full">
          {videos.length}
        </span>
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
        />
        <QuickPlayPanel
          title="Oldest Shorts"
          icon={BoltIcon}
          videos={shortVideos}
          isLoading={shorts.isLoading}
          emptyMessage="No saved shorts found. Save shorts from your inbox to see them here."
        />
      </div>
    </div>
  );
}
