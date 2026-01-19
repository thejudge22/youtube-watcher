# Implementation Plan: Frontend Error Boundary UX

**Goal:** Improve the user experience when an error occurs by providing actionable options (Retry, Go Home) in the Error Boundary.
**Current State:** The application uses a generic `ErrorBoundary` component, but the UI for the fallback state needs verification and enhancement to be "user-friendly".
**Approach:** Update the `ErrorFallback` component to include interactive elements.

## 1. Analyze Existing Component

The file `frontend/src/components/common/ErrorBoundary.tsx` handles errors. We need to check if `ErrorFallback` is a separate component or defined inline, and update it.

## 2. Enhance ErrorFallback UI

*   **File:** `frontend/src/components/common/ErrorFallback.tsx` (or inside `ErrorBoundary.tsx` if inline).
*   **Changes:**
    1.  **Styling:** Ensure the error message is centered and styled consistently with the dark theme (Tailwind classes).
    2.  **Retry Action:**
        *   Accept a `resetErrorBoundary` prop (passed by `react-error-boundary` or the custom generic boundary).
        *   Add a button: `<Button onClick={resetErrorBoundary}>Try Again</Button>`.
    3.  **Navigation Action:**
        *   Add a "Return to Home" button.
        *   **Note:** Since `ErrorBoundary` wraps the `BrowserRouter` in `App.tsx` (in some places) or is inside it in others, using `useNavigate` might not always be safe if the error occurred *outside* the router context.
        *   **Safe Approach:** Use a simple `window.location.href = '/'` for a hard reset, or standard anchor tag `<a href="/">` if strictly outside context. However, looking at `App.tsx`, `ErrorBoundary` is used *inside* `BrowserRouter` for routes. In those cases, `useNavigate` is safe.
        *   **Hybrid:** If the component is within the Router context, provide a nice Link. If not, a hard reload button.

## 3. Implementation Details

Update `frontend/src/components/common/ErrorFallback.tsx`:

```tsx
import { Button } from './Button'; // Assuming Button component exists

interface ErrorFallbackProps {
  error: Error;
  resetErrorBoundary: () => void;
}

export function ErrorFallback({ error, resetErrorBoundary }: ErrorFallbackProps) {
  return (
    <div className="flex flex-col items-center justify-center min-h-[50vh] p-8 text-center">
      <div className="bg-red-900/20 p-6 rounded-lg border border-red-800/50 max-w-lg w-full">
        <h2 className="text-xl font-semibold text-red-400 mb-2">
          Something went wrong
        </h2>
        <pre className="text-sm text-red-200/70 mb-6 overflow-auto max-h-40 bg-black/30 p-2 rounded text-left">
          {error.message}
        </pre>
        <div className="flex gap-4 justify-center">
          <Button onClick={resetErrorBoundary} variant="primary">
            Try Again
          </Button>
          <Button onClick={() => window.location.href = '/'} variant="secondary">
            Go Home
          </Button>
        </div>
      </div>
    </div>
  );
}
```

*   **Update:** `frontend/src/components/common/ErrorBoundary.tsx` to use this new/updated fallback UI.

## 4. Verification

*   **Manual Test:** Temporarily introduce a bug (e.g., `throw new Error("Test")` in a component like `Inbox.tsx`).
*   **Verify:**
    *   The error UI appears.
    *   "Try Again" resets the state (removes the error boundary if the error was transient).
    *   "Go Home" navigates to the root URL.
