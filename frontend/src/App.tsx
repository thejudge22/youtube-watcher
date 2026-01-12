import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Header } from './components/layout/Header';
import { Navigation } from './components/layout/Navigation';
import { Inbox } from './pages/Inbox';
import { Saved } from './pages/Saved';
import { Channels } from './pages/Channels';
import { Settings } from './pages/Settings';

function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-900">
        <Header />
        <Navigation />
        <main>
          <Routes>
            <Route path="/" element={<Inbox />} />
            <Route path="/saved" element={<Saved />} />
            <Route path="/channels" element={<Channels />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}

export default App;
