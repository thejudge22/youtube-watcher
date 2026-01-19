import type { Channel } from '../../types';
import { Button } from '../common/Button';
import { useDeleteChannel, useRefreshChannel } from '../../hooks/useChannels';

interface ChannelListViewProps {
  channels: Channel[];
}

function formatDate(dateString: string | null): string {
  if (!dateString) return 'Never';
  const date = new Date(dateString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));

  // Handle future dates (clock skew, etc.)
  if (diffDays < 0) return 'Just now';
  if (diffDays === 0) return 'Today';
  if (diffDays === 1) return 'Yesterday';
  if (diffDays < 7) return `${diffDays} days ago`;
  return date.toLocaleDateString();
}

export function ChannelListView({ channels }: ChannelListViewProps) {
  const deleteChannel = useDeleteChannel();
  const refreshChannel = useRefreshChannel();

  if (channels.length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg p-8 text-center text-gray-400">
        <p>No channels added yet.</p>
        <p className="mt-2 text-sm">Add a YouTube channel to start tracking.</p>
      </div>
    );
  }

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden">
      {/* Table Header */}
      <div className="grid grid-cols-12 gap-4 px-6 py-3 bg-gray-700/50 border-b border-gray-700 text-sm font-medium text-gray-300">
        <div className="col-span-1">Thumbnail</div>
        <div className="col-span-3">Channel Name</div>
        <div className="col-span-2">Videos</div>
        <div className="col-span-2">Last Checked</div>
        <div className="col-span-4 text-right">Actions</div>
      </div>

      {/* Table Body */}
      <div className="divide-y divide-gray-700">
        {channels.map((channel) => (
          <div
            key={channel.id}
            className="grid grid-cols-12 gap-4 px-6 py-4 items-center hover:bg-gray-700/30 transition-colors"
          >
            {/* Thumbnail */}
            <div className="col-span-1">
              <img
                src={channel.thumbnail_url || '/placeholder-channel.png'}
                alt={channel.name}
                className="w-12 h-12 rounded-full object-cover"
              />
            </div>

            {/* Channel Name */}
            <div className="col-span-3 min-w-0">
              <h3 className="text-white font-medium truncate">{channel.name}</h3>
              <a
                href={channel.youtube_url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:text-blue-300 text-sm flex items-center gap-1 mt-0.5"
              >
                <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M11 3a1 1 0 100 2h2.586l-6.293 6.293a1 1 0 101.414 1.414L15 6.414V9a1 1 0 102 0V4a1 1 0 00-1-1h-5z" />
                  <path d="M5 5a2 2 0 00-2 2v8a2 2 0 002 2h8a2 2 0 002-2v-3a1 1 0 10-2 0v3H5V7h3a1 1 0 000-2H5z" />
                </svg>
                View on YouTube
              </a>
            </div>

            {/* Video Count */}
            <div className="col-span-2">
              <span className="text-gray-300">
                {channel.video_count} video{channel.video_count !== 1 ? 's' : ''}
              </span>
            </div>

            {/* Last Checked */}
            <div className="col-span-2">
              <span className="text-gray-400 text-sm">
                {formatDate(channel.last_checked)}
              </span>
            </div>

            {/* Actions */}
            <div className="col-span-4 flex items-center justify-end gap-2">
              <Button
                variant="secondary"
                onClick={() => refreshChannel.mutate(channel.id)}
                disabled={refreshChannel.isPending}
                title="Refresh channel"
                className="p-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
              </Button>
              <Button
                variant="danger"
                onClick={() => {
                  if (window.confirm(`Are you sure you want to delete "${channel.name}"?`)) {
                    deleteChannel.mutate(channel.id);
                  }
                }}
                disabled={deleteChannel.isPending}
                title="Delete channel"
                className="p-2"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </Button>
            </div>
          </div>
        ))}
      </div>

      {/* Footer with count */}
      <div className="px-6 py-3 bg-gray-700/30 border-t border-gray-700 text-sm text-gray-400">
        {channels.length} channel{channels.length !== 1 ? 's' : ''}
      </div>
    </div>
  );
}
