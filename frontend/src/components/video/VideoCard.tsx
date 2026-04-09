import { useState } from 'react';
import type { Video } from '../../types';
import { Button } from '../common/Button';
import { ViewMode } from '../common/ViewModeToggle';
import { ShortsBadge } from './ShortsBadge';
import { 
  CheckCircleIcon, 
  XCircleIcon,
  PlayIcon,
  ArrowTopRightOnSquareIcon
} from '@heroicons/react/24/outline';

interface VideoCardProps {
  video: Video;
  onSave?: (id: string) => void;
  onDiscard: (id: string) => void;
  showSaveButton?: boolean;
  showDiscardButton?: boolean;
  viewMode?: ViewMode;
  isSelectionMode?: boolean;
  isSelected?: boolean;
  onToggleSelect?: (id: string, shiftKey: boolean) => void;
  // Touch drag selection props
  touchProps?: object;
  selectZoneProps?: object;
  isInPreviewRange?: boolean;
  isDragStart?: boolean;
  isDragEnd?: boolean;
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
  touchProps,
  selectZoneProps,
  isInPreviewRange = false,
  isDragStart = false,
  isDragEnd = false,
}: VideoCardProps) {
  const [imageLoaded, setImageLoaded] = useState(false);

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
    const getDragFeedbackClasses = () => {
      if (isDragStart) return 'ring-2 ring-accent-blue shadow-glow-blue';
      if (isDragEnd) return 'ring-2 ring-accent-blue/70';
      if (isInPreviewRange) return 'bg-accent-blue/10 ring-1 ring-accent-blue/50';
      return '';
    };

    return (
      <div
        className={`flex items-center gap-4 p-3 bg-bg-secondary rounded-xl border border-transparent hover:border-border transition-all duration-200 ${getDragFeedbackClasses()}`}
        {...touchProps}
      >
        {/* Checkbox - only visible in selection mode */}
        {isSelectionMode && (
          <div 
            className="flex-shrink-0 self-stretch flex items-center pl-2 pr-4 -ml-2 -my-3 cursor-pointer touch-none"
            {...selectZoneProps}
          >
            <input
              type="checkbox"
              checked={isSelected}
              onChange={(e) => onToggleSelect?.(video.id, (e.nativeEvent as MouseEvent).shiftKey)}
              className="w-5 h-5 rounded-md border-border bg-bg-tertiary text-accent-blue focus:ring-2 focus:ring-accent-blue focus:ring-offset-0 cursor-pointer transition-all"
            />
          </div>
        )}

        {/* Thumbnail - fixed width */}
        <a
          href={video.video_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-shrink-0 w-44 group"
        >
          <div className="aspect-video rounded-lg overflow-hidden bg-bg-tertiary relative">
            {!imageLoaded && (
              <div className="absolute inset-0 shimmer" />
            )}
            {video.thumbnail_url ? (
              <>
                <img
                  src={video.thumbnail_url}
                  alt={video.title}
                  className={`w-full h-full object-cover transition-all duration-300 group-hover:scale-105 ${
                    imageLoaded ? 'opacity-100' : 'opacity-0'
                  }`}
                  loading="lazy"
                  onLoad={() => setImageLoaded(true)}
                />
                {/* Play overlay on hover */}
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center justify-center">
                  <PlayIcon className="w-8 h-8 text-white" />
                </div>
              </>
            ) : (
              <div className="w-full h-full flex items-center justify-center text-text-tertiary text-xs">
                <PlayIcon className="w-6 h-6" />
              </div>
            )}
            {/* Shorts badge */}
            {video.is_short && (
              <ShortsBadge className="absolute top-2 left-2" />
            )}
          </div>
        </a>

        {/* Content - flexible */}
        <div className="flex-1 min-w-0">
          <a
            href={video.video_url}
            target="_blank"
            rel="noopener noreferrer"
            className="font-medium text-text-primary hover:text-accent-blue transition-colors line-clamp-1 block group/link"
          >
            {video.title}
            <ArrowTopRightOnSquareIcon className="w-3.5 h-3.5 inline-block ml-1.5 opacity-0 group-hover/link:opacity-100 transition-opacity text-text-tertiary" />
          </a>
          <div className="text-sm text-text-secondary mt-1.5 flex items-center flex-wrap gap-x-2">
            {video.channel_name && (
              <span className="font-medium text-text-secondary">{video.channel_name}</span>
            )}
            <span className="text-text-tertiary">{formatDate(video.published_at)}</span>
            {video.saved_at && (
              <span className="text-accent-blue text-xs bg-accent-blue/10 px-2 py-0.5 rounded-full">
                Saved {formatSavedDate(video.saved_at)}
              </span>
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
                size="sm"
                className="gap-1"
              >
                <CheckCircleIcon className="w-4 h-4" />
                Save
              </Button>
            )}
            {showDiscardButton && (
              <Button
                variant="danger"
                onClick={() => onDiscard(video.id)}
                size="sm"
                className="gap-1"
              >
                <XCircleIcon className="w-4 h-4" />
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
    const getDragFeedbackClasses = () => {
      if (isDragStart) return 'ring-2 ring-accent-blue shadow-glow-blue';
      if (isDragEnd) return 'ring-2 ring-accent-blue/70';
      if (isInPreviewRange) return 'bg-accent-blue/10 ring-1 ring-accent-blue/50';
      return '';
    };

    return (
      <div className="flex items-start gap-2 h-full">
        {/* Checkbox - only visible in selection mode */}
        {isSelectionMode && (
          <div 
            className="flex-shrink-0 self-stretch flex items-center px-2 -ml-2 cursor-pointer touch-none"
            {...selectZoneProps}
          >
            <input
              type="checkbox"
              checked={isSelected}
              onChange={(e) => onToggleSelect?.(video.id, (e.nativeEvent as MouseEvent).shiftKey)}
              className="w-5 h-5 rounded-md border-border bg-bg-tertiary text-accent-blue focus:ring-2 focus:ring-accent-blue focus:ring-offset-0 cursor-pointer transition-all"
            />
          </div>
        )}

        <div
          className={`flex-1 flex flex-col bg-bg-secondary rounded-xl overflow-hidden border border-transparent hover:border-border transition-all duration-300 relative h-full group ${getDragFeedbackClasses()} ${!isSelectionMode ? 'hover:-translate-y-1 hover:shadow-lg' : ''}`}
          {...touchProps}
        >
          {/* Thumbnail - fixed aspect ratio */}
          <a
            href={video.video_url}
            target="_blank"
            rel="noopener noreferrer"
            className="flex-shrink-0"
          >
            <div className="aspect-video relative bg-bg-tertiary overflow-hidden">
              {!imageLoaded && (
                <div className="absolute inset-0 shimmer" />
              )}
              {video.thumbnail_url ? (
                <>
                  <img
                    src={video.thumbnail_url}
                    alt={video.title}
                    className={`w-full h-full object-cover transition-transform duration-300 group-hover:scale-105 ${
                      imageLoaded ? 'opacity-100' : 'opacity-0'
                    }`}
                    loading="lazy"
                    onLoad={() => setImageLoaded(true)}
                  />
                  {/* Play overlay on hover */}
                  <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center justify-center">
                    <PlayIcon className="w-8 h-8 text-white" />
                  </div>
                </>
              ) : (
                <div className="w-full h-full flex items-center justify-center text-text-tertiary text-xs">
                  <PlayIcon className="w-6 h-6" />
                </div>
              )}
              {/* Shorts badge */}
              {video.is_short && (
                <ShortsBadge className="absolute top-2 left-2" />
              )}
            </div>
          </a>

          {/* Content - fills remaining space */}
          <div className="p-2.5 flex-1 flex flex-col min-h-0">
            <a
              href={video.video_url}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm font-medium text-text-primary hover:text-accent-blue transition-colors line-clamp-2 block"
            >
              {video.title}
            </a>
            <div className="text-xs text-text-tertiary mt-1.5">
              {formatDate(video.published_at)}
            </div>
            {/* Action buttons at bottom - not overlay */}
            {!isSelectionMode && (showSaveButton && onSave || showDiscardButton) && (
              <div className="flex gap-2 mt-auto pt-2">
                {showSaveButton && onSave && (
                  <Button
                    variant="primary"
                    onClick={() => onSave(video.id)}
                    size="sm"
                    className="flex-1 gap-1"
                  >
                    <CheckCircleIcon className="w-3.5 h-3.5" />
                    Save
                  </Button>
                )}
                {showDiscardButton && (
                  <Button
                    variant="danger"
                    onClick={() => onDiscard(video.id)}
                    size="sm"
                    className={showSaveButton && onSave ? 'flex-1 gap-1' : 'w-full gap-1'}
                  >
                    <XCircleIcon className="w-3.5 h-3.5" />
                    {showSaveButton && onSave ? 'Discard' : 'Remove'}
                  </Button>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Large view (default) - original layout with improvements
  const getDragFeedbackClasses = () => {
    if (isDragStart) return 'ring-2 ring-accent-blue shadow-glow-blue';
    if (isDragEnd) return 'ring-2 ring-accent-blue/70';
    if (isInPreviewRange) return 'bg-accent-blue/10 ring-1 ring-accent-blue/50';
    return '';
  };

  return (
    <div className="flex items-start gap-2 h-full">
      {/* Checkbox - only visible in selection mode */}
      {isSelectionMode && (
        <div 
          className="flex-shrink-0 self-stretch flex items-center px-2 -ml-2 cursor-pointer"
          {...selectZoneProps}
        >
          <input
            type="checkbox"
            checked={isSelected}
            onChange={(e) => onToggleSelect?.(video.id, (e.nativeEvent as MouseEvent).shiftKey)}
            className="w-5 h-5 rounded-md border-border bg-bg-tertiary text-accent-blue focus:ring-2 focus:ring-accent-blue focus:ring-offset-0 cursor-pointer pointer-events-none transition-all"
          />
        </div>
      )}

      <div
        className={`flex-1 flex flex-col bg-bg-secondary rounded-xl overflow-hidden border border-transparent hover:border-border transition-all duration-300 h-full group ${getDragFeedbackClasses()} ${!isSelectionMode ? 'hover:-translate-y-1 hover:shadow-lg' : ''}`}
        {...touchProps}
      >
        {/* Thumbnail - fixed aspect ratio */}
        <a
          href={video.video_url}
          target="_blank"
          rel="noopener noreferrer"
          className="flex-shrink-0"
        >
          <div className="aspect-video relative bg-bg-tertiary overflow-hidden">
            {!imageLoaded && (
              <div className="absolute inset-0 shimmer" />
            )}
            {video.thumbnail_url ? (
              <>
                <img
                  src={video.thumbnail_url}
                  alt={video.title}
                  className={`w-full h-full object-cover transition-transform duration-300 group-hover:scale-105 ${
                    imageLoaded ? 'opacity-100' : 'opacity-0'
                  }`}
                  loading="lazy"
                  onLoad={() => setImageLoaded(true)}
                />
                {/* Play overlay on hover */}
                <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center justify-center">
                  <PlayIcon className="w-10 h-10 text-white" />
                </div>
              </>
            ) : (
              <div className="w-full h-full flex items-center justify-center text-text-tertiary">
                <PlayIcon className="w-10 h-10" />
              </div>
            )}
            {/* Shorts badge */}
            {video.is_short && (
              <ShortsBadge className="absolute top-3 left-3" />
            )}
          </div>
        </a>

        {/* Content - fills remaining space */}
        <div className="p-4 flex-1 flex flex-col min-h-0">
          <a
            href={video.video_url}
            target="_blank"
            rel="noopener noreferrer"
            className="block group/link"
          >
            <h3 className="text-text-primary font-medium line-clamp-2 hover:text-accent-blue transition-colors">
              {video.title}
            </h3>
          </a>

          <div className="mt-auto pt-3 space-y-1">
            {video.channel_name && (
              <p className="text-text-secondary text-sm font-medium">{video.channel_name}</p>
            )}
            <p className="text-text-tertiary text-xs">
              Published: {formatDate(video.published_at)}
            </p>
            {video.saved_at && (
              <p className="text-accent-blue text-xs bg-accent-blue/10 inline-block px-2 py-0.5 rounded-full">
                Saved: {formatSavedDate(video.saved_at)}
              </p>
            )}
            {!isSelectionMode && (showSaveButton && onSave || showDiscardButton) && (
              <div className="flex space-x-2 mt-4 pt-2">
                {showSaveButton && onSave && (
                  <Button
                    variant="primary"
                    onClick={() => onSave(video.id)}
                    className={showDiscardButton ? 'flex-1' : 'w-full'}
                    size="sm"
                  >
                    <CheckCircleIcon className="w-4 h-4 mr-1.5" />
                    Save
                  </Button>
                )}
                {showDiscardButton && (
                  <Button
                    variant="danger"
                    onClick={() => onDiscard(video.id)}
                    className={showSaveButton && onSave ? 'flex-1' : 'w-full'}
                    size="sm"
                  >
                    <XCircleIcon className="w-4 h-4 mr-1.5" />
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
