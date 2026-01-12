import { useDiscardedVideos, useSaveVideo } from '../../hooks/useVideos';
import { Modal } from '../common/Modal';
import { VideoList } from './VideoList';
import { LoadingSpinner } from '../common/LoadingSpinner';

interface RecentlyDeletedModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function RecentlyDeletedModal({ isOpen, onClose }: RecentlyDeletedModalProps) {
  const { data: videos, isLoading, error } = useDiscardedVideos(30);
  const saveVideo = useSaveVideo();

  const handleSave = (id: string) => {
    saveVideo.mutate(id, {
      onSuccess: () => {
        // The video will automatically disappear from this list when refetched
      },
    });
  };

  const handleDiscard = () => {
    // Do nothing - videos are already discarded
    // This button won't be shown in the VideoList
  };

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Recently Deleted">
      <div className="mt-4">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <LoadingSpinner size="lg" />
          </div>
        ) : error ? (
          <div className="bg-red-900/50 border border-red-700 rounded-lg p-4 text-center">
            <p className="text-red-400">Error loading recently deleted videos.</p>
          </div>
        ) : videos && videos.length > 0 ? (
          <>
            <p className="text-gray-400 text-sm mb-4">
              Videos deleted in the last 30 days. Click "Save" to restore them.
            </p>
            <div className="max-h-[60vh] overflow-y-auto">
              <VideoList
                videos={videos}
                onSave={handleSave}
                onDiscard={handleDiscard}
                showSaveButton={true}
                showDiscardButton={false}
                emptyMessage="No recently deleted videos."
              />
            </div>
          </>
        ) : (
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
                d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
              />
            </svg>
            <h3 className="mt-2 text-lg font-medium text-white">No deleted videos</h3>
            <p className="mt-1 text-sm text-gray-400">
              Videos you remove will appear here for 30 days.
            </p>
          </div>
        )}
      </div>
    </Modal>
  );
}