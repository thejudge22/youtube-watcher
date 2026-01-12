import React from 'react';
import type { Video } from '../../types';
import { Button } from '../common/Button';

interface VideoCardProps {
  video: Video;
  onSave?: (id: string) => void;
  onDiscard: (id: string) => void;
  showSaveButton?: boolean;
}

export function VideoCard({ video, onSave, onDiscard, showSaveButton = true }: VideoCardProps) {
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
    }).format(date);
  };

  const formatSavedDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    }).format(date);
  };

  return (
    <div className="bg-gray-800 rounded-lg overflow-hidden hover:bg-gray-750 transition-colors">
      <a
        href={video.video_url}
        target="_blank"
        rel="noopener noreferrer"
        className="block"
      >
        <div className="aspect-video relative bg-gray-700">
          {video.thumbnail_url ? (
            <img
              src={video.thumbnail_url}
              alt={video.title}
              className="w-full h-full object-cover"
              loading="lazy"
            />
          ) : (
            <div className="w-full h-full flex items-center justify-center text-gray-500">
              No thumbnail
            </div>
          )}
        </div>
      </a>
      <div className="p-4">
        <a
          href={video.video_url}
          target="_blank"
          rel="noopener noreferrer"
          className="block"
        >
          <h3 className="text-white font-medium line-clamp-2 hover:text-blue-400 transition-colors">
            {video.title}
          </h3>
        </a>
        {video.channel_name && (
          <p className="text-gray-400 text-sm mt-1">{video.channel_name}</p>
        )}
        <p className="text-gray-500 text-xs mt-1">
          Published: {formatDate(video.published_at)}
        </p>
        {video.saved_at && (
          <p className="text-blue-400 text-xs mt-1">
            Saved: {formatSavedDate(video.saved_at)}
          </p>
        )}
        <div className="flex space-x-2 mt-4">
          {showSaveButton && onSave && (
            <Button
              variant="primary"
              onClick={() => onSave(video.id)}
              className="flex-1"
            >
              Save
            </Button>
          )}
          <Button
            variant="danger"
            onClick={() => onDiscard(video.id)}
            className={showSaveButton && onSave ? 'flex-1' : 'w-full'}
          >
            {showSaveButton && onSave ? 'Discard' : 'Remove'}
          </Button>
        </div>
      </div>
    </div>
  );
}