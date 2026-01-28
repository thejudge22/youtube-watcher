import { useState } from 'react';
import { useSavedVideos, useBulkDiscardVideos, useDiscardedVideos, usePurgeAllDiscarded } from '../hooks/useVideos';
import { Button } from '../components/common/Button';
import { Modal } from '../components/common/Modal';
import ImportExportSection from '../components/settings/ImportExportSection';
import AppSettingsSection from '../components/settings/AppSettingsSection';
import { BackupSettingsSection } from '../components/settings/BackupSettingsSection';

export function Settings() {
  const { data: savedVideosData } = useSavedVideos({ limit: 100, offset: 0 });
  const { data: discardedVideos } = useDiscardedVideos();
  const bulkDiscard = useBulkDiscardVideos();
  const purgeAllDiscarded = usePurgeAllDiscarded();
  const [isConfirmModalOpen, setIsConfirmModalOpen] = useState(false);
  const [isPurgeConfirmModalOpen, setIsPurgeConfirmModalOpen] = useState(false);
  const [showDangerZone, setShowDangerZone] = useState(false);

  const videos = savedVideosData?.videos ?? [];

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

  const handlePurgeAll = () => {
    purgeAllDiscarded.mutate(undefined, {
      onSuccess: () => {
        setIsPurgeConfirmModalOpen(false);
      },
    });
  };

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <h1 className="text-2xl font-bold text-white mb-6">Settings</h1>

      {/* Application Settings Section */}
      <div className="bg-gray-800 rounded-lg p-6 shadow-lg mb-6">
        <AppSettingsSection />
      </div>

      {/* Issue #12: Scheduled Backups Section */}
      <div className="bg-gray-800 rounded-lg p-6 shadow-lg mb-6">
        <BackupSettingsSection />
      </div>

      {/* Import/Export Section */}
      <div className="bg-gray-800 rounded-lg p-6 shadow-lg mb-6">
        <ImportExportSection />
      </div>

      <div className="bg-gray-800 rounded-lg p-6 shadow-lg">
        <h2 className="text-lg font-medium text-white mb-4">Data Management</h2>
        <p className="text-gray-400 mb-6">
          Manage your saved videos and application data.
        </p>
        
        <div className="border-t border-gray-700 pt-6">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="text-md font-medium text-white">Data Removal</h3>
              <p className="text-sm text-gray-400">
                Actions that remove or permanently delete data.
              </p>
            </div>
            <Button
              variant="secondary"
              onClick={() => setShowDangerZone(!showDangerZone)}
            >
              {showDangerZone ? 'Hide' : 'Show'}
            </Button>
          </div>

          {showDangerZone && (
            <div className="space-y-4 mt-4">
              <div className="bg-red-900/20 border border-red-700/50 rounded-lg p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-md font-medium text-red-400">Purge All Recently Deleted Videos</h3>
                    <p className="text-sm text-red-300/70">
                      Permanently delete all videos in the recently deleted list. This action cannot be undone.
                    </p>
                  </div>
                  <Button
                    variant="danger"
                    onClick={() => setIsPurgeConfirmModalOpen(true)}
                    disabled={!discardedVideos || discardedVideos.length === 0}
                  >
                    Purge All
                  </Button>
                </div>
              </div>
            </div>
          )}
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

      <Modal
        isOpen={isPurgeConfirmModalOpen}
        onClose={() => setIsPurgeConfirmModalOpen(false)}
        title="⚠️ Permanent Deletion Warning"
      >
        <div className="mt-2">
          <p className="text-sm text-gray-300 mb-3">
            Are you sure you want to <span className="font-bold text-red-400">permanently delete</span> all recently deleted videos?
          </p>
          <p className="text-sm text-gray-400">
            This will delete <span className="font-semibold text-white">{discardedVideos?.length || 0}</span> video(s) from the recently deleted list.
          </p>
          <p className="text-sm text-red-400 font-semibold mt-3">
            This action cannot be undone!
          </p>
        </div>

        <div className="mt-6 flex space-x-3 justify-end">
          <Button
            variant="secondary"
            onClick={() => setIsPurgeConfirmModalOpen(false)}
          >
            Cancel
          </Button>
          <Button
            variant="danger"
            onClick={handlePurgeAll}
            isLoading={purgeAllDiscarded.isPending}
          >
            Yes, Permanently Delete All
          </Button>
        </div>
      </Modal>
    </div>
  );
}