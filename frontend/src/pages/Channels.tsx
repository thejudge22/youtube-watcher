import { useState, useEffect } from 'react';
import { 
  TvIcon, 
  PlusIcon, 
  Squares2X2Icon, 
  ListBulletIcon 
} from '@heroicons/react/24/outline';
import { useChannels } from '../hooks/useChannels';
import { ChannelList } from '../components/channel/ChannelList';
import { ChannelListView } from '../components/channel/ChannelListView';
import { AddChannelModal } from '../components/channel/AddChannelModal';
import { Button } from '../components/common/Button';
import { LoadingSpinner } from '../components/common/LoadingSpinner';

type ViewMode = 'grid' | 'list';

const VIEW_MODE_KEY = 'channelsViewMode';

export function Channels() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [viewMode, setViewMode] = useState<ViewMode>(() => {
    const saved = localStorage.getItem(VIEW_MODE_KEY);
    return (saved === 'list' || saved === 'grid') ? saved : 'grid';
  });
  const { data: channels, isLoading, error } = useChannels();

  useEffect(() => {
    localStorage.setItem(VIEW_MODE_KEY, viewMode);
  }, [viewMode]);

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-accent-purple to-accent-blue flex items-center justify-center shadow-lg">
            <TvIcon className="w-5 h-5 text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-text-primary">Channels</h1>
            {channels && channels.length > 0 && (
              <p className="text-text-secondary text-sm">
                {channels.length} channel{channels.length !== 1 ? 's' : ''} tracked
              </p>
            )}
          </div>
        </div>
        
        <div className="flex items-center gap-3">
          {/* View Toggle */}
          <div className="flex items-center bg-bg-secondary rounded-lg p-1 border border-border">
            <button
              onClick={() => setViewMode('grid')}
              className={`p-2 rounded-md transition-all duration-200 ${
                viewMode === 'grid'
                  ? 'bg-bg-tertiary text-text-primary shadow-sm'
                  : 'text-text-tertiary hover:text-text-secondary'
              }`}
              aria-label="Grid view"
              title="Grid view"
            >
              <Squares2X2Icon className="w-5 h-5" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={`p-2 rounded-md transition-all duration-200 ${
                viewMode === 'list'
                  ? 'bg-bg-tertiary text-text-primary shadow-sm'
                  : 'text-text-tertiary hover:text-text-secondary'
              }`}
              aria-label="List view"
              title="List view"
            >
              <ListBulletIcon className="w-5 h-5" />
            </button>
          </div>
          
          <Button onClick={() => setIsModalOpen(true)} size="sm">
            <PlusIcon className="w-4 h-4 mr-1.5" />
            Add Channel
          </Button>
        </div>
      </div>

      {/* Loading */}
      {isLoading && (
        <div className="flex flex-col items-center justify-center py-16 gap-4">
          <LoadingSpinner size="lg" />
          <p className="text-text-secondary text-sm animate-pulse">Loading channels...</p>
        </div>
      )}

      {/* Error */}
      {error && (
        <div className="bg-accent-red/10 border border-accent-red/30 rounded-xl p-6 text-center animate-scale-in">
          <div className="w-12 h-12 bg-accent-red/20 rounded-full flex items-center justify-center mx-auto mb-3">
            <TvIcon className="w-6 h-6 text-accent-red" />
          </div>
          <p className="text-accent-red font-medium">Failed to load channels</p>
          <p className="text-text-secondary text-sm mt-1">
            {error instanceof Error ? error.message : 'Please try again later'}
          </p>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !error && channels?.length === 0 && (
        <div className="flex flex-col items-center justify-center py-16 text-center animate-scale-in">
          <div className="w-20 h-20 rounded-2xl bg-bg-secondary flex items-center justify-center mb-4">
            <TvIcon className="w-10 h-10 text-text-tertiary" />
          </div>
          <h3 className="text-lg font-semibold text-text-primary mb-1">No channels yet</h3>
          <p className="text-text-secondary text-sm max-w-sm mb-6">
            Add YouTube channels to start tracking their videos. New videos will automatically appear in your inbox.
          </p>
          <Button onClick={() => setIsModalOpen(true)}>
            <PlusIcon className="w-4 h-4 mr-1.5" />
            Add Your First Channel
          </Button>
        </div>
      )}

      {/* Content */}
      {!isLoading && !error && channels && channels.length > 0 && (
        <div className="animate-slide-up">
          {viewMode === 'grid' ? (
            <ChannelList channels={channels} />
          ) : (
            <ChannelListView channels={channels} />
          )}
        </div>
      )}

      <AddChannelModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </div>
  );
}
