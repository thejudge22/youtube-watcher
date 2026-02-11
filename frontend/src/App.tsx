import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Header } from './components/layout/Header';
import { Navigation } from './components/layout/Navigation';
import { Inbox } from './pages/Inbox';
import { Saved } from './pages/Saved';
import { Channels } from './pages/Channels';
import { Settings } from './pages/Settings';
import { Login } from './pages/Login';
import { ErrorBoundary } from './components/common/ErrorBoundary';
import { PWAUpdatePrompt } from './components/common/PWAUpdatePrompt';
import { useTheme } from './hooks/useTheme';
import { AuthProvider, useAuth } from './context/AuthContext';

/**
 * Main application content with authentication check
 * Shows Login page if auth is required and user is not authenticated
 * Shows the main app otherwise
 */
function AppContent() {
  const { theme, toggleTheme } = useTheme();
  const { isAuthEnabled, isAuthenticated, isLoading } = useAuth();

  // Show loading state while checking auth status
  if (isLoading) {
    return (
      <div className="min-h-screen bg-bg-primary flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <svg 
            className="animate-spin h-10 w-10 text-accent-red" 
            xmlns="http://www.w3.org/2000/svg" 
            fill="none" 
            viewBox="0 0 24 24"
          >
            <circle 
              className="opacity-25" 
              cx="12" 
              cy="12" 
              r="10" 
              stroke="currentColor" 
              strokeWidth="4"
            />
            <path 
              className="opacity-75" 
              fill="currentColor" 
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          <p className="text-text-secondary">Loading...</p>
        </div>
      </div>
    );
  }

  // Show login page if auth is enabled but user is not authenticated
  if (isAuthEnabled && !isAuthenticated) {
    return <Login />;
  }

  // Show main application
  return (
    <ErrorBoundary componentName="Application">
      <BrowserRouter>
        <div className="min-h-screen bg-bg-primary transition-colors duration-200">
          <PWAUpdatePrompt />
          <ErrorBoundary componentName="Header">
            <Header theme={theme} onToggleTheme={toggleTheme} />
          </ErrorBoundary>
          <ErrorBoundary componentName="Navigation">
            <Navigation />
          </ErrorBoundary>
          <main className="pb-12">
            <Routes>
              <Route
                path="/"
                element={
                  <ErrorBoundary componentName="Inbox">
                    <Inbox />
                  </ErrorBoundary>
                }
              />
              <Route
                path="/saved"
                element={
                  <ErrorBoundary componentName="Saved Videos">
                    <Saved />
                  </ErrorBoundary>
                }
              />
              <Route
                path="/channels"
                element={
                  <ErrorBoundary componentName="Channels">
                    <Channels />
                  </ErrorBoundary>
                }
              />
              <Route
                path="/settings"
                element={
                  <ErrorBoundary componentName="Settings">
                    <Settings />
                  </ErrorBoundary>
                }
              />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </ErrorBoundary>
  );
}

/**
 * Root application component with AuthProvider
 */
function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
