import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Header } from './components/layout/Header';
import { Navigation } from './components/layout/Navigation';
import { Inbox } from './pages/Inbox';
import { Saved } from './pages/Saved';
import { Channels } from './pages/Channels';
import { Settings } from './pages/Settings';
import { ErrorBoundary } from './components/common/ErrorBoundary';

function App() {
  return (
    <ErrorBoundary componentName="Application">
      <BrowserRouter>
        <div className="min-h-screen bg-gray-900">
          <ErrorBoundary componentName="Header">
            <Header />
          </ErrorBoundary>
          <ErrorBoundary componentName="Navigation">
            <Navigation />
          </ErrorBoundary>
          <main>
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

export default App;
