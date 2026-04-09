import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { useAddChannel } from '../../hooks/useChannels';

interface AddChannelModalProps {
  isOpen: boolean;
  onClose: () => void;
}

/**
 * Normalize channel input to a full YouTube URL.
 * Supports:
 * - Full URLs: https://youtube.com/@channel, https://youtube.com/c/channel, etc.
 * - Bare handles: @channel
 * - Channel names (auto-converted to handle format)
 */
function normalizeChannelInput(input: string): string {
  const trimmed = input.trim();

  // If it's already a full URL, return as-is
  if (trimmed.startsWith('http://') || trimmed.startsWith('https://')) {
    return trimmed;
  }

  // If it's a bare handle (@channel), prepend YouTube URL
  if (trimmed.startsWith('@')) {
    return `https://www.youtube.com/${trimmed}`;
  }

  // If it looks like a channel name without @, treat it as a handle
  // This handles cases like user typing "Games_for_James" instead of "@Games_for_James"
  return `https://www.youtube.com/@${trimmed}`;
}

export function AddChannelModal({ isOpen, onClose }: AddChannelModalProps) {
  const [url, setUrl] = useState('');
  const addChannel = useAddChannel();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    // Normalize the input to a full YouTube URL
    const normalizedUrl = normalizeChannelInput(url.trim());

    try {
      await addChannel.mutateAsync(normalizedUrl);
      setUrl('');
      onClose();
    } catch {
      // Error is handled by the mutation
    }
  };

  const handleClose = () => {
    setUrl('');
    onClose();
  };

  const isLoading = addChannel.isPending;
  const error = addChannel.error;

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Add YouTube Channel">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label
            htmlFor="channelUrl"
            className="block text-sm font-medium text-text-secondary mb-1"
          >
            Channel URL or Handle
          </label>
          <input
            id="channelUrl"
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://youtube.com/@channel or @handle"
            className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-md text-text-primary placeholder-text-tertiary focus:outline-none focus:ring-2 focus:ring-accent-blue focus:border-transparent"
            disabled={isLoading}
          />
          <p className="mt-1 text-xs text-gray-500">
            Paste a full YouTube URL (https://youtube.com/@channel) or just the handle (@channel)
          </p>
        </div>

        {error && (
          <div className="p-3 bg-red-900/50 border border-red-700 rounded-md">
            <p className="text-sm text-red-300">
              {(error as any)?.errorCode === 'CHANNEL_ALREADY_EXISTS'
                ? 'This channel has already been added'
                : (error as any)?.errorMessage
                  ? (error as any).errorMessage
                  : error instanceof Error
                    ? error.message
                    : 'Failed to add channel'}
            </p>
          </div>
        )}

        <div className="flex justify-end space-x-3 pt-2">
          <Button
            type="button"
            variant="secondary"
            onClick={handleClose}
            disabled={isLoading}
          >
            Cancel
          </Button>
          <Button type="submit" isLoading={isLoading}>
            Add Channel
          </Button>
        </div>
      </form>
    </Modal>
  );
}