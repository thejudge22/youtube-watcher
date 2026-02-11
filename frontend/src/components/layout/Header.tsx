import { useState } from 'react';
import { Link } from 'react-router-dom';
import { PlusIcon } from '@heroicons/react/24/outline';
import { AddVideoModal } from '../video/AddVideoModal';
import { Button } from '../common/Button';
import { ThemeToggle } from '../common/ThemeToggle';
import type { Theme } from '../../hooks/useTheme';

interface HeaderProps {
  theme: Theme;
  onToggleTheme: () => void;
}

export function Header({ theme, onToggleTheme }: HeaderProps) {
  const [isAddVideoModalOpen, setIsAddVideoModalOpen] = useState(false);

  return (
    <>
      <header className="glass sticky top-0 z-50 border-b border-border">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-accent-red to-accent-orange flex items-center justify-center shadow-glow">
                <svg 
                  className="w-5 h-5 text-white" 
                  fill="currentColor" 
                  viewBox="0 0 20 20"
                >
                  <path d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" />
                </svg>
              </div>
              <Link 
                to="/" 
                className="text-xl font-bold gradient-text tracking-tight hover:opacity-90 transition-opacity"
              >
                YouTube Watcher
              </Link>
            </div>

            {/* Actions */}
            <div className="flex items-center space-x-3">
              <ThemeToggle theme={theme} onToggle={onToggleTheme} />
              <Button
                onClick={() => setIsAddVideoModalOpen(true)}
                size="sm"
                className="gap-1.5"
              >
                <PlusIcon className="w-4 h-4" />
                Add URL
              </Button>
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
