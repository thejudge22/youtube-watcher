import { useState } from 'react';
import type { Video } from '../../types';
import { Button } from '../common/Button';
import { ViewMode } from '../common/ViewModeToggle';
import { ShortsBadge } from './ShortsBadge';

interface VideoCardProps {
  video: Video;
  onSave?: (id: string) => void;
  onDiscard: (id: string) => void;
  showSaveButton?: boolean;
  showDiscardButton?: boolean;
  viewMode?: ViewMode;
  isSelectionMode?: boolean;
  isSelected?: boolean;
  onToggleSelect?: (id: string) => void;
}

export function VideoCard({
  video,
  onSave,
  onDiscard,
  showSaveButton = true,
  showDiscardButton = true,
  viewMode = 'large',
  isSelectionMode = false,
  isSelected = false,
  onToggleSelect,
}: VideoCardProps) {
  const [isHovered, setIsHovered] = useState(false);
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

  // List view - horizontal layout
  if (viewMode === 'list') {
    return (
      <div className="flex items-center gap-4 p-2 bg-gray-800 rounded-lg hover:bg-gray-750 transition-colors">
        {/* Checkbox - only visible in selection mode */}
        {isSelectionMode && (
          <div className="flex-shrink-0">
            <input
              type="checkbox"
              checked={isSelected}
              onChange={() => onToggleSelect?.(video.id)}
              className="w-5 h-5 rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 cursor-pointer"
            />
          </div>
        )}

        {/* Thumbnail - fixed width */}
        <a
          href={video.video_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-shrink-0 w-40"
        >
          <div className="aspect-video rounded overflow-hidden bg-gray-700 relative">
            {video.thumbnail_url ? (
              <img
                src={video.thumbnail_url}
                alt={video.title}
                className="w-full h-full object-cover"
                loading="lazy"
              />
            ) : (
              <div className="w-full h-full flex items-center justify-center text-gray-500 text-xs">
                No thumbnail
              </div>
            )}
            {/* Issue #8: Shorts badge */}
            {video.is_short && (
              <ShortsBadge className="absolute top-1 left-1" />
            )}
          </div>
        </a>

        {/* Content - flexible */}
        <div className="flex-1 min-w-0">
          <a
            href={video.video_url}
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-white hover:text-blue-400 line-clamp-1 block"
          >
            {video.title}
          </a>
          <div className="text-sm text-gray-400 mt-1">
            {video.channel_name && (
              <>
                <span>{video.channel_name}</span>
                <span className="mx-2">•</span>
              </>
            )}
            <span>{formatDate(video.published_at)}</span>
            {video.saved_at && (
              <>
                <span className="mx-2">•</span>
                <span className="text-blue-400">Saved {formatSavedDate(video.saved_at)}</span>
              </>
            )}
          </div>
        </div>

        {/* Actions - fixed right */}
        {!isSelectionMode && (showSaveButton && onSave || showDiscardButton) && (
          <div className="flex-shrink-0 flex gap-2">
            {showSaveButton && onSave && (
              <Button
                variant="primary"
                onClick={() => onSave(video.id)}
                className="text-sm px-3 py-1"
              >
                Save
              </Button>
            )}
            {showDiscardButton && (
              <Button
                variant="danger"
                onClick={() => onDiscard(video.id)}
                className="text-sm px-3 py-1"
              >
                {showSaveButton && onSave ? 'Discard' : 'Remove'}
              </Button>
            )}
          </div>
        )}
      </div>
    );
  }

  // Compact view - smaller cards with hover actions
  if (viewMode === 'compact') {
    return (
      <div className="flex items-start gap-2 h-full">
        {/* Checkbox - only visible in selection mode */}
        {isSelectionMode && (
          <div className="flex-shrink-0 self-center">
            <input
              type="checkbox"
              checked={isSelected}
              onChange={() => onToggleSelect?.(video.id)}
              className="w-5 h-5 rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 cursor-pointer"
            />
          </div>
        )}

        <div
          className="flex-1 flex flex-col bg-gray-800 rounded-lg overflow-hidden hover:bg-gray-750 transition-colors relative h-full"
          onMouseEnter={() => setIsHovered(true)}
          onMouseLeave={() => setIsHovered(false)}
        >
          {/* Thumbnail - fixed aspect ratio */}
          <a
            href={video.video_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-shrink-0"
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
                <div className="w-full h-full flex items-center justify-center text-gray-500 text-xs">
                  No thumbnail
                </div>
              )}
              {/* Issue #8: Shorts badge */}
              {video.is_short && (
                <ShortsBadge className="absolute top-1 left-1" />
              )}
            </div>
          </a>

          {/* Content - fills remaining space */}
          <div className="p-2 flex-1 flex flex-col min-h-0">
            <a
              href={video.video_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm font-medium text-white hover:text-blue-400 line-clamp-2 block"
            >
              {video.title}
            </a>
            <div className="text-xs text-gray-400 mt-1">
              {formatDate(video.published_at)}
            </div>
          </div>

          {/* Hover actions overlay */}
          {!isSelectionMode && isHovered && (showSaveButton && onSave || showDiscardButton) && (
            <div className="absolute inset-0 bg-black/60 flex items-center justify-center gap-2">
              {showSaveButton && onSave && (
                <Button
                  variant="primary"
                  onClick={() => onSave(video.id)}
                  className="text-sm px-3 py-1"
                >
                  Save
                </Button>
              )}
              {showDiscardButton && (
                <Button
                  variant="danger"
                  onClick={() => onDiscard(video.id)}
                  className="text-sm px-3 py-1"
                >
                  {showSaveButton && onSave ? 'Discard' : 'Remove'}
                </Button>
              )}
            </div>
          )}
        </div>
      </div>
    );
  }

  // Large view (default) - original layout
  return (
    <div className="flex items-start gap-2 h-full">
      {/* Checkbox - only visible in selection mode */}
      {isSelectionMode && (
        <div className="flex-shrink-0 self-center">
          <input
            type="checkbox"
            checked={isSelected}
            onChange={() => onToggleSelect?.(video.id)}
            className="w-5 h-5 rounded border-gray-600 bg-gray-700 text-blue-600 focus:ring-2 focus:ring-blue-500 focus:ring-offset-0 cursor-pointer"
          />
        </div>
      )}

      <div className="flex-1 flex flex-col bg-gray-800 rounded-lg overflow-hidden hover:bg-gray-750 transition-colors h-full">
        {/* Thumbnail - fixed aspect ratio */}
        <a
          href={video.video_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-shrink-0"
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
            {/* Issue #8: Shorts badge */}
            {video.is_short && (
              <ShortsBadge className="absolute top-2 left-2" />
            )}
          </div>
        </a>

        {/* Content - fills remaining space */}
        <div className="p-4 flex-1 flex flex-col min-h-0">
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

          <div className="mt-auto pt-3">
            {video.channel_name && (
              <p className="text-gray-400 text-sm">{video.channel_name}</p>
            )}
            <p className="text-gray-500 text-xs mt-1">
              Published: {formatDate(video.published_at)}
            </p>
            {video.saved_at && (
              <p className="text-blue-400 text-xs mt-1">
                Saved: {formatSavedDate(video.saved_at)}
              </p>
            )}
            {!isSelectionMode && (showSaveButton && onSave || showDiscardButton) && (
              <div className="flex space-x-2 mt-4">
                {showSaveButton && onSave && (
                  <Button
                    variant="primary"
                    onClick={() => onSave(video.id)}
                    className={showDiscardButton ? 'flex-1' : 'w-full'}
                  >
                    Save
                  </Button>
                )}
                {showDiscardButton && (
                  <Button
                    variant="danger"
                    onClick={() => onDiscard(video.id)}
                    className={showSaveButton && onSave ? 'flex-1' : 'w-full'}
                  >
                    {showSaveButton && onSave ? 'Discard' : 'Remove'}
                  </Button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
