import { useState } from 'react';
import { NavLink } from 'react-router-dom';
import {
  InboxIcon,
  BookmarkIcon,
  PlayIcon,
  TvIcon,
  Cog6ToothIcon,
  PlusIcon,
  ArrowRightOnRectangleIcon,
} from '@heroicons/react/24/outline';
import { useInboxVideos } from '../../hooks/useVideos';
import { useAuth } from '../../context/AuthContext';
import { AddVideoModal } from '../video/AddVideoModal';
import { ThemeToggle } from '../common/ThemeToggle';
import { AppLogo } from './AppLogo';
import type { Theme } from '../../hooks/useTheme';

interface NavItem {
  to: string;
  label: string;
  icon: React.ElementType;
}

const mainItems: NavItem[] = [
  { to: '/', label: 'Inbox', icon: InboxIcon },
  { to: '/saved', label: 'Saved', icon: BookmarkIcon },
  { to: '/quickplay', label: 'QuickPlay', icon: PlayIcon },
  { to: '/channels', label: 'Channels', icon: TvIcon },
];

const settingsItem: NavItem = { to: '/settings', label: 'Settings', icon: Cog6ToothIcon };

function useInboxCount() {
  const { data: inboxVideos } = useInboxVideos(undefined, 'all');
  return inboxVideos?.length ?? 0;
}

function formatCount(count: number) {
  return count > 99 ? '99+' : String(count);
}

function SidebarLink({ item, count }: { item: NavItem; count?: number }) {
  return (
    <NavLink
      to={item.to}
      end={item.to === '/'}
      className={({ isActive }) =>
        `flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
          isActive
            ? 'bg-bg-tertiary text-text-primary'
            : 'text-text-secondary hover:text-text-primary hover:bg-bg-tertiary/60'
        }`
      }
    >
      {({ isActive }) => (
        <>
          <item.icon className={`w-5 h-5 ${isActive ? 'text-accent-red' : ''}`} />
          <span className="flex-1">{item.label}</span>
          {count !== undefined && count > 0 && (
            <span className="text-xs font-semibold text-accent-red tabular-nums">
              {formatCount(count)}
            </span>
          )}
        </>
      )}
    </NavLink>
  );
}

interface SidebarProps {
  theme: Theme;
  onToggleTheme: () => void;
}

/** Desktop navigation: fixed left sidebar, shown from the lg breakpoint. */
export function Sidebar({ theme, onToggleTheme }: SidebarProps) {
  const inboxCount = useInboxCount();
  const { isAuthEnabled, logout } = useAuth();
  const [isAddVideoModalOpen, setIsAddVideoModalOpen] = useState(false);

  return (
    <>
      <aside className="hidden lg:flex fixed inset-y-0 left-0 z-40 w-56 flex-col bg-bg-secondary border-r border-border">
        <div className="px-5 h-16 flex items-center">
          <AppLogo />
        </div>

        <div className="px-3">
          <button
            onClick={() => setIsAddVideoModalOpen(true)}
            className="w-full flex items-center justify-center gap-2 px-3 py-2 rounded-lg text-sm font-medium bg-accent-red hover:bg-accent-red-hover text-white transition-colors"
          >
            <PlusIcon className="w-4 h-4" />
            Add URL
          </button>
        </div>

        <nav className="flex-1 px-3 mt-4 space-y-1" aria-label="Main">
          {mainItems.map((item) => (
            <SidebarLink
              key={item.to}
              item={item}
              count={item.to === '/' ? inboxCount : undefined}
            />
          ))}
        </nav>

        <div className="px-3 py-4 space-y-1 border-t border-border">
          <SidebarLink item={settingsItem} />
          <div className="flex items-center justify-between px-1 pt-2">
            <ThemeToggle theme={theme} onToggle={onToggleTheme} />
            {isAuthEnabled && (
              <button
                onClick={logout}
                className="flex items-center gap-1.5 px-2 py-1.5 rounded-lg text-sm text-text-secondary hover:text-text-primary hover:bg-bg-tertiary transition-colors"
                title="Log out"
              >
                <ArrowRightOnRectangleIcon className="w-4 h-4" />
                Log out
              </button>
            )}
          </div>
        </div>
      </aside>
      <AddVideoModal
        isOpen={isAddVideoModalOpen}
        onClose={() => setIsAddVideoModalOpen(false)}
      />
    </>
  );
}

/** Phone and tablet navigation: fixed bottom tab bar, hidden from lg up. */
export function MobileTabBar() {
  const inboxCount = useInboxCount();

  return (
    <nav
      className="lg:hidden fixed bottom-0 inset-x-0 z-40 glass border-t border-border pb-[env(safe-area-inset-bottom)]"
      aria-label="Main"
    >
      <div className="grid grid-cols-5">
        {[...mainItems, settingsItem].map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            end={item.to === '/'}
            className={({ isActive }) =>
              `relative flex flex-col items-center gap-0.5 pt-2 pb-1.5 text-[11px] font-medium transition-colors ${
                isActive ? 'text-accent-red' : 'text-text-secondary hover:text-text-primary'
              }`
            }
          >
            <item.icon className="w-6 h-6" />
            <span>{item.label}</span>
            {item.to === '/' && inboxCount > 0 && (
              <span className="absolute top-1 left-1/2 ml-2 min-w-[1.1rem] h-[1.1rem] px-1 rounded-full bg-accent-red text-white text-[10px] font-semibold flex items-center justify-center tabular-nums">
                {formatCount(inboxCount)}
              </span>
            )}
          </NavLink>
        ))}
      </div>
    </nav>
  );
}
