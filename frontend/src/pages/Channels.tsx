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
import { PageHeader } from '../components/layout/PageHeader';
import { segmentedGroup, segmentedItem } from '../components/common/segmented';

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
      <PageHeader
        title="Channels"
        subtitle={
          channels && channels.length > 0
            ? `${channels.length} channel${channels.length !== 1 ? 's' : ''} tracked`
            : undefined
        }
        actions={
          <>
          {/* View Toggle */}
          <div className={segmentedGroup} role="group" aria-label="View mode">
            <button
              onClick={() => setViewMode('grid')}
              className={segmentedItem(viewMode === 'grid')}
              aria-label="Grid view"
              title="Grid view"
            >
              <Squares2X2Icon className="w-4 h-4" />
            </button>
            <button
              onClick={() => setViewMode('list')}
              className={segmentedItem(viewMode === 'list')}
              aria-label="List view"
              title="List view"
            >
              <ListBulletIcon className="w-4 h-4" />
            </button>
          </div>
          
          <Button onClick={() => setIsModalOpen(true)} size="sm">
            <PlusIcon className="w-4 h-4 mr-1.5" />
            Add Channel
          </Button>
          </>
        }
      />

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
