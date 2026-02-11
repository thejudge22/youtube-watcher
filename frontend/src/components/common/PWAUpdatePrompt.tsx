import { useRegisterSW } from 'virtual:pwa-register/react';

/**
 * PWA Update Prompt Component
 * 
 * Shows a toast notification when:
 * - The app is ready to work offline
 * - A new version is available and the user should reload
 * 
 * Uses vite-plugin-pwa's virtual module for service worker registration
 */
export function PWAUpdatePrompt() {
  const {
    needRefresh: [needRefresh, setNeedRefresh],
    offlineReady: [offlineReady, setOfflineReady],
    updateServiceWorker,
  } = useRegisterSW({
    immediate: true,  // Register the service worker immediately
    onRegistered(registration) {
      console.log('SW Registered:', registration);
    },
    onRegisterError(error) {
      console.error('SW registration error:', error);
    },
  });

  const closePrompt = () => {
    setOfflineReady(false);
    setNeedRefresh(false);
  };

  const handleUpdate = () => {
    updateServiceWorker();
    setNeedRefresh(false);
  };

  // Don't render if no notification needed
  if (!offlineReady && !needRefresh) {
    return null;
  }

  return (
    <div className="fixed bottom-4 left-4 right-4 md:left-auto md:right-4 md:w-96 z-50 animate-slide-up">
      <div className="bg-surface border border-border rounded-lg shadow-lg p-4 flex items-start gap-3">
        <div className="flex-shrink-0 mt-0.5">
          {needRefresh ? (
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5 text-accent-red"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"
              />
            </svg>
          ) : (
            <svg
              xmlns="http://www.w3.org/2000/svg"
              className="h-5 w-5 text-green-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M5 13l4 4L19 7"
              />
            </svg>
          )}
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-sm font-medium text-text-primary">
            {needRefresh ? 'Update Available' : 'Offline Ready'}
          </p>
          <p className="text-sm text-text-secondary mt-1">
            {needRefresh
              ? 'A new version is available. Click reload to update.'
              : 'App is ready to work offline.'}
          </p>
          <div className="flex gap-2 mt-3">
            {needRefresh && (
              <button
                onClick={handleUpdate}
                className="px-3 py-1.5 bg-accent-red hover:bg-accent-red-hover text-white text-sm font-medium rounded transition-colors"
              >
                Reload
              </button>
            )}
            <button
              onClick={closePrompt}
              className="px-3 py-1.5 bg-surface-hover hover:bg-border text-text-primary text-sm font-medium rounded transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
