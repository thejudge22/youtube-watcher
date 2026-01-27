import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { useAddChannel } from '../../hooks/useChannels';

interface AddChannelModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AddChannelModal({ isOpen, onClose }: AddChannelModalProps) {
  const [url, setUrl] = useState('');
  const addChannel = useAddChannel();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    try {
      await addChannel.mutateAsync(url.trim());
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
            className="block text-sm font-medium text-gray-300 mb-1"
          >
            Channel URL or Handle
          </label>
          <input
            id="channelUrl"
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://youtube.com/@channel or @handle"
            className="w-full px-3 py-2 bg-gray-700 border border-gray-600 rounded-md text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            disabled={isLoading}
          />
          <p className="mt-1 text-xs text-gray-500">
            Paste a YouTube channel URL, handle, or custom URL
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