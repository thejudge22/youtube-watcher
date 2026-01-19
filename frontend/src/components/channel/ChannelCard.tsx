import type { Channel } from '../../types';
import { Button } from '../common/Button';
import { useDeleteChannel, useRefreshChannel } from '../../hooks/useChannels';

interface ChannelCardProps {
  channel: Channel;
}

export function ChannelCard({ channel }: ChannelCardProps) {
  const deleteChannel = useDeleteChannel();
  const refreshChannel = useRefreshChannel();

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
        <a
          href={channel.youtube_url}
          target="_blank"
          rel="noopener noreferrer"
          className="text-blue-400 hover:text-blue-300 text-sm mt-1 inline-flex items-center gap-1"
        >
          <svg
            className="w-4 h-4"
            fill="currentColor"
            viewBox="0 0 20 20"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z" />
            <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z" />
          </svg>
          View on YouTube
        </a>
        <p className="text-gray-400 text-sm mt-1">
          {channel.video_count} video{channel.video_count !== 1 ? 's' : ''}
        </p>
        {channel.last_checked && (
          <p className="text-gray-500 text-xs mt-1">
            Last checked: {new Date(channel.last_checked).toLocaleDateString()}
          </p>
        )}
      </div>
      <div className="flex items-center gap-2">
        <Button
          variant="secondary"
          onClick={() => refreshChannel.mutate(channel.id)}
          disabled={refreshChannel.isPending}
          className="p-2"
          title="Refresh channel"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
        </Button>
        <Button
          variant="danger"
          onClick={handleDelete}
          disabled={deleteChannel.isPending}
          className="p-2"
          title="Delete channel"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </Button>
      </div>
    </div>
  );
}