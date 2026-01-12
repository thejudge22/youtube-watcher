import type { Channel } from '../../types';
import { Button } from '../common/Button';
import { useDeleteChannel } from '../../hooks/useChannels';

interface ChannelCardProps {
  channel: Channel;
}

export function ChannelCard({ channel }: ChannelCardProps) {
  const deleteChannel = useDeleteChannel();

  const handleDelete = () => {
    if (window.confirm(`Are you sure you want to delete "${channel.name}"?`)) {
      deleteChannel.mutate(channel.id);
    }
  };

  return (
    <div className="bg-gray-800 rounded-lg p-4 flex items-start space-x-4">
      <img
        src={channel.thumbnail_url || '/placeholder-channel.png'}
        alt={channel.name}
        className="w-16 h-16 rounded-full object-cover flex-shrink-0"
      />
      <div className="flex-1 min-w-0">
        <h3 className="text-white font-medium truncate">{channel.name}</h3>
        <p className="text-gray-400 text-sm mt-1">
          {channel.video_count} video{channel.video_count !== 1 ? 's' : ''}
        </p>
        {channel.last_checked && (
          <p className="text-gray-500 text-xs mt-1">
            Last checked: {new Date(channel.last_checked).toLocaleDateString()}
          </p>
        )}
      </div>
      <Button
        variant="danger"
        onClick={handleDelete}
        disabled={deleteChannel.isPending}
        className="flex-shrink-0"
      >
        Delete
      </Button>
    </div>
  );
}