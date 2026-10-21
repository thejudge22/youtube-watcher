import { useState } from 'react';
import { PlusIcon, ArrowRightOnRectangleIcon } from '@heroicons/react/24/outline';
import { AddVideoModal } from '../video/AddVideoModal';
import { ThemeToggle } from '../common/ThemeToggle';
import { AppLogo } from './AppLogo';
import { useAuth } from '../../context/AuthContext';
import type { Theme } from '../../hooks/useTheme';

interface HeaderProps {
  theme: Theme;
  onToggleTheme: () => void;
}

/** Top bar for phones and tablets; the desktop sidebar replaces it from lg up. */
export function Header({ theme, onToggleTheme }: HeaderProps) {
  const [isAddVideoModalOpen, setIsAddVideoModalOpen] = useState(false);
  const { isAuthEnabled, logout } = useAuth();

  return (
    <>
      <header className="lg:hidden glass sticky top-0 z-40 border-b border-border">
        <div className="px-4 h-14 flex items-center justify-between">
          <AppLogo />
          <div className="flex items-center gap-1">
            <ThemeToggle theme={theme} onToggle={onToggleTheme} />
            {isAuthEnabled && (
              <button
                onClick={logout}
                className="p-2 rounded-lg text-text-secondary hover:text-text-primary hover:bg-bg-tertiary transition-colors"
                title="Log out"
                aria-label="Log out"
              >
                <ArrowRightOnRectangleIcon className="w-5 h-5" />
              </button>
            )}
            <button
              onClick={() => setIsAddVideoModalOpen(true)}
              className="ml-1 flex items-center gap-1 px-3 py-1.5 rounded-lg text-sm font-medium bg-accent-red hover:bg-accent-red-hover text-white transition-colors"
            >
              <PlusIcon className="w-4 h-4" />
              Add
            </button>
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
