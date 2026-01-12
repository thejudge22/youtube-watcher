import { useState } from 'react';
import { useChannels } from '../hooks/useChannels';
import { ChannelList } from '../components/channel/ChannelList';
import { AddChannelModal } from '../components/channel/AddChannelModal';
import { Button } from '../components/common/Button';
import { LoadingSpinner } from '../components/common/LoadingSpinner';

export function Channels() {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const { data: channels, isLoading, error } = useChannels();

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-2xl font-bold text-white">Channels</h1>
        <Button onClick={() => setIsModalOpen(true)}>
          Add Channel
        </Button>
      </div>

      {isLoading && (
        <div className="flex justify-center py-12">
          <LoadingSpinner size="lg" />
        </div>
      )}

      {error && (
        <div className="bg-red-900/50 border border-red-700 rounded-lg p-4 text-center">
          <p className="text-red-300">Failed to load channels</p>
          <p className="text-red-400 text-sm mt-1">
            {error instanceof Error ? error.message : 'Please try again later'}
          </p>
        </div>
      )}

      {!isLoading && !error && (
        <ChannelList channels={channels || []} />
      )}

      <AddChannelModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
      />
    </div>
  );
}