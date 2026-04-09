import React, { useState } from 'react';
import { Modal } from '../common/Modal';
import { Button } from '../common/Button';
import { useAddVideoFromUrl } from '../../hooks/useVideos';

interface AddVideoModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function AddVideoModal({ isOpen, onClose }: AddVideoModalProps) {
  const [url, setUrl] = useState('');
  const addVideo = useAddVideoFromUrl();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!url.trim()) return;

    try {
      await addVideo.mutateAsync(url.trim());
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

  const isLoading = addVideo.isPending;
  const error = addVideo.error;

  return (
    <Modal isOpen={isOpen} onClose={handleClose} title="Add YouTube Video">
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label
            htmlFor="videoUrl"
            className="block text-sm font-medium text-text-secondary mb-1"
          >
            Video URL
          </label>
          <input
            id="videoUrl"
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://youtube.com/watch?v=..."
            className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-md text-text-primary placeholder-text-tertiary focus:outline-none focus:ring-2 focus:ring-accent-blue focus:border-transparent"
            disabled={isLoading}
          />
          <p className="mt-1 text-xs text-gray-500">
            Paste a YouTube video URL to save it to your library
          </p>
        </div>

        {error && (
          <div className="p-3 bg-red-900/50 border border-red-700 rounded-md">
            <p className="text-sm text-red-300">
              {error instanceof Error ? error.message : 'Failed to add video'}
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
            Add Video
          </Button>
        </div>
      </form>
    </Modal>
  );
}