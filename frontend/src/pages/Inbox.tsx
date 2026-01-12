import { useInboxVideos, useSaveVideo, useDiscardVideo, useBulkSaveVideos, useBulkDiscardVideos, useRefreshAllChannels } from '../hooks/useVideos';
import { VideoList } from '../components/video/VideoList';
import { Button } from '../components/common/Button';
import { LoadingSpinner } from '../components/common/LoadingSpinner';

export function Inbox() {
  const { data: videos, isLoading, error, refetch } = useInboxVideos();
  const saveVideo = useSaveVideo();
  const discardVideo = useDiscardVideo();
  const bulkSave = useBulkSaveVideos();
  const bulkDiscard = useBulkDiscardVideos();
  const refreshAll = useRefreshAllChannels();

  const handleSave = (id: string) => {
    saveVideo.mutate(id);
  };

  const handleDiscard = (id: string) => {
    discardVideo.mutate(id);
  };

  const handleSaveAll = () => {
    if (videos && videos.length > 0) {
      const videoIds = videos.map((v) => v.id);
      bulkSave.mutate(videoIds);
    }
  };

  const handleDiscardAll = () => {
    if (videos && videos.length > 0) {
      const videoIds = videos.map((v) => v.id);
      bulkDiscard.mutate(videoIds);
    }
  };

  const handleRefresh = () => {
    refreshAll.mutate(undefined, {
      onSuccess: () => {
        refetch();
      },
    });
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-900/50 border border-red-700 rounded-lg p-4 text-center">
          <p className="text-red-400">Error loading videos. Please try again.</p>
          <Button
            variant="secondary"
            onClick={() => refetch()}
            className="mt-4"
          >
            Retry
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Inbox</h1>
          {videos && videos.length > 0 && (
            <p className="text-gray-400 text-sm mt-1">
              {videos.length} video{videos.length !== 1 ? 's' : ''} to review
            </p>
          )}
        </div>
        <div className="flex space-x-3">
          <Button
            variant="secondary"
            onClick={handleRefresh}
            isLoading={refreshAll.isPending}
          >
            Refresh
          </Button>
          {videos && videos.length > 0 && (
            <>
              <Button
                variant="primary"
                onClick={handleSaveAll}
                isLoading={bulkSave.isPending}
              >
                Save All
              </Button>
              <Button
                variant="danger"
                onClick={handleDiscardAll}
                isLoading={bulkDiscard.isPending}
              >
                Discard All
              </Button>
            </>
          )}
        </div>
      </div>

      <VideoList
        videos={videos || []}
        onSave={handleSave}
        onDiscard={handleDiscard}
        emptyMessage="No videos in inbox. Add channels to start receiving video updates."
      />
    </div>
  );
}