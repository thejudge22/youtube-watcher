import { useState } from 'react';
import { useSavedVideos, useBulkDiscardVideos } from '../hooks/useVideos';
import { Button } from '../components/common/Button';
import { Modal } from '../components/common/Modal';

export function Settings() {
  const { data: videos } = useSavedVideos();
  const bulkDiscard = useBulkDiscardVideos();
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);

  const handleRemoveAll = () => {
    if (videos && videos.length > 0) {
      const videoIds = videos.map((v) => v.id);
      bulkDiscard.mutate(videoIds, {
        onSuccess: () => {
          setIsConfirmModalOpen(false);
        },
      });
    }
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-white mb-6">Settings</h1>
      
      <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
        <h2 className="text-lg font-medium text-white mb-4">Data Management</h2>
        <p className="text-gray-400 mb-6">
          Manage your saved videos and application data.
        </p>
        
        <div className="border-t border-gray-700 pt-6">
          <div className="flex items-center justify-between">
            <div>
              <h3 className="text-md font-medium text-white">Remove All Saved Videos</h3>
              <p className="text-sm text-gray-400">
                This will move all your currently saved videos to the recently deleted list.
              </p>
            </div>
            <Button
              variant="danger"
              onClick={() => setIsConfirmModalOpen(true)}
              disabled={!videos || videos.length === 0}
            >
              Remove All
            </Button>
          </div>
        </div>
      </div>

      <Modal
        isOpen={isConfirmModalOpen}
        onClose={() => setIsConfirmModalOpen(false)}
        title="Are You Sure?"
      >
        <div className="mt-2">
          <p className="text-sm text-gray-300">
            Are you sure you want to remove all saved videos? They will be moved to the Recently Deleted list where you can restore them for up to 30 days.
          </p>
        </div>

        <div className="mt-6 flex space-x-3 justify-end">
          <Button
            variant="secondary"
            onClick={() => setIsConfirmModalOpen(false)}
          >
            Cancel
          </Button>
          <Button
            variant="danger"
            onClick={handleRemoveAll}
            isLoading={bulkDiscard.isPending}
          >
            Yes, Remove All
          </Button>
        </div>
      </Modal>
    </div>
  );
}