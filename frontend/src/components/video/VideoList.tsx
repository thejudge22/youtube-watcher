import React from 'react';
import type { Video } from '../../types';
import { VideoCard } from './VideoCard';

interface VideoListProps {
  videos: Video[];
  onSave?: (id: string) => void;
  onDiscard: (id: string) => void;
  emptyMessage?: string;
  showSaveButton?: boolean;
}

export function VideoList({ videos, onSave, onDiscard, emptyMessage, showSaveButton = true }: VideoListProps) {
  if (videos.length === 0) {
    return (
      <div className="bg-gray-800 rounded-lg p-12 text-center">
        <svg
          className="mx-auto h-12 w-12 text-gray-500"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z"
          />
        </svg>
        <h3 className="mt-2 text-lg font-medium text-white">No videos found</h3>
        <p className="mt-1 text-sm text-gray-400">
          {emptyMessage || 'No videos to display.'}
        </p>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
      {videos.map((video) => (
        <VideoCard
          key={video.id}
          video={video}
          onSave={onSave}
          onDiscard={onDiscard}
          showSaveButton={showSaveButton}
        />
      ))}
    </div>
  );
}