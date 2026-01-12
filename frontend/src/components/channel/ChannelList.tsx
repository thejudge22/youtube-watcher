import type { Channel } from '../../types';
import { ChannelCard } from './ChannelCard';

interface ChannelListProps {
  channels: Channel[];
}

export function ChannelList({ channels }: ChannelListProps) {
  if (channels.length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg p-8 text-center text-gray-400">
        <p>No channels added yet.</p>
        <p className="mt-2 text-sm">Add a YouTube channel to start tracking.</p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {channels.map((channel) => (
        <ChannelCard key={channel.id} channel={channel} />
      ))}
    </div>
  );
}