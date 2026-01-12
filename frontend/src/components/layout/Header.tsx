import { useState } from 'react';
import { Link } from 'react-router-dom';
import { AddVideoModal } from '../video/AddVideoModal';

export function Header() {
  const [isAddVideoModalOpen, setIsAddVideoModalOpen] = useState(false);

  return (
    <>
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <Link to="/" className="text-xl font-bold text-red-500">
                YouTube Watcher
              </Link>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setIsAddVideoModalOpen(true)}
                className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium rounded-md transition-colors"
              >
                Add URL
              </button>
            </div>
          </div>
        </div>
      </header>
      <AddVideoModal
        isOpen={isAddVideoModalOpen}
        onClose={() => setIsAddVideoModalOpen(false)}
      />
    </>
  );
}