import type { Channel } from '../../types';
import { Button } from '../common/Button';
import { useDeleteChannel, useRefreshChannel } from '../../hooks/useChannels';
import { 
  ArrowTopRightOnSquareIcon, 
  ArrowPathIcon, 
  TrashIcon,
  VideoCameraIcon 
} from '@heroicons/react/24/outline';

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
    <div className="group bg-bg-secondary rounded-xl p-4 border border-transparent hover:border-border transition-all duration-300 hover:-translate-y-1 hover:shadow-lg">
      <div className="flex items-start space-x-4">
        {/* Channel Avatar */}
        <div className="relative flex-shrink-0">
          <div className="w-16 h-16 rounded-full overflow-hidden bg-bg-tertiary ring-2 ring-transparent group-hover:ring-border transition-all duration-300">
            <img
              src={channel.thumbnail_url || '/placeholder-channel.png'}
              alt={channel.name}
              className="w-full h-full object-cover transition-transform duration-300 group-hover:scale-110"
            />
          </div>
          {/* Online indicator */}
          <div className="absolute -bottom-0.5 -right-0.5 w-4 h-4 bg-bg-secondary rounded-full flex items-center justify-center">
            <div className="w-2.5 h-2.5 bg-accent-green rounded-full" />
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <h3 className="text-text-primary font-semibold truncate group-hover:text-accent-blue transition-colors">
            {channel.name}
          </h3>
          
          <a
            href={channel.youtube_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-text-secondary hover:text-accent-blue text-sm mt-1 inline-flex items-center gap-1 transition-colors group/link"
          >
            <span>View on YouTube</span>
            <ArrowTopRightOnSquareIcon className="w-3.5 h-3.5 opacity-0 group-hover/link:opacity-100 transition-opacity" />
          </a>
          
          <div className="flex items-center gap-3 mt-2">
            <span className="inline-flex items-center gap-1.5 text-text-tertiary text-xs bg-bg-tertiary px-2.5 py-1 rounded-full">
              <VideoCameraIcon className="w-3.5 h-3.5" />
              {channel.video_count} video{channel.video_count !== 1 ? 's' : ''}
            </span>
            {channel.last_checked && (
              <span className="text-text-tertiary text-xs">
                Checked {new Date(channel.last_checked).toLocaleDateString()}
              </span>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
          <Button
            variant="ghost"
            onClick={() => refreshChannel.mutate(channel.id)}
            disabled={refreshChannel.isPending}
            size="sm"
            className="p-2"
            title="Refresh channel"
          >
            <ArrowPathIcon className={`w-4 h-4 ${refreshChannel.isPending ? 'animate-spin' : ''}`} />
          </Button>
          <Button
            variant="ghost"
            onClick={handleDelete}
            disabled={deleteChannel.isPending}
            size="sm"
            className="p-2 text-accent-red hover:text-accent-red hover:bg-accent-red/10"
            title="Delete channel"
          >
            <TrashIcon className="w-4 h-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
