import { Button } from './Button';

interface ErrorFallbackProps {
  error: Error;
  resetError: () => void;
  componentName?: string;
}

export function ErrorFallback({ error, resetError, componentName }: ErrorFallbackProps) {
  return (
    <div className="min-h-[400px] flex items-center justify-center p-6">
      <div className="bg-red-900/20 border border-red-500/50 rounded-lg p-6 max-w-2xl">
        <div className="flex items-start gap-4">
          <div className="flex-shrink-0">
            <svg
              className="w-8 h-8 text-red-500"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
              />
            </svg>
          </div>
          <div className="flex-1">
            <h2 className="text-xl font-semibold text-red-400 mb-2">
              {componentName ? `Error in ${componentName}` : 'Something went wrong'}
            </h2>
            <p className="text-gray-300 mb-4">
              An unexpected error occurred. You can try reloading this section or the entire page.
            </p>
            {import.meta.env.DEV && (
              <details className="mb-4">
                <summary className="text-sm text-gray-400 cursor-pointer hover:text-gray-300">
                  Error details (development only)
                </summary>
                <pre className="mt-2 text-xs text-gray-400 bg-gray-900 p-3 rounded overflow-x-auto">
                  {error.message}
                  {error.stack && `\n\n${error.stack}`}
                </pre>
              </details>
            )}
            <div className="flex gap-3">
              <Button onClick={resetError} variant="primary">
                Try Again
              </Button>
              <Button onClick={() => window.location.reload()} variant="secondary">
                Reload Page
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
