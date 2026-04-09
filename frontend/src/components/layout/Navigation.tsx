import { NavLink } from 'react-router-dom';
import { 
  InboxIcon, 
  BookmarkIcon, 
  TvIcon, 
  Cog6ToothIcon 
} from '@heroicons/react/24/outline';

interface NavItem {
  to: string;
  label: string;
  icon: React.ElementType;
}

const navItems: NavItem[] = [
  { to: '/', label: 'Inbox', icon: InboxIcon },
  { to: '/saved', label: 'Saved', icon: BookmarkIcon },
  { to: '/channels', label: 'Channels', icon: TvIcon },
  { to: '/settings', label: 'Settings', icon: Cog6ToothIcon },
];

export function Navigation() {
  return (
    <nav className="bg-bg-secondary border-b border-border">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex space-x-1">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `relative py-4 px-4 font-medium text-sm transition-all duration-200 rounded-t-lg group flex items-center gap-2 ${
                  isActive
                    ? 'text-text-primary'
                    : 'text-text-secondary hover:text-text-primary hover:bg-bg-tertiary/50'
                }`
              }
            >
              {({ isActive }) => (
                <>
                  <item.icon 
                    className={`w-4 h-4 transition-transform duration-200 ${
                      isActive ? 'text-accent-red' : 'group-hover:scale-110'
                    }`} 
                  />
                  <span>{item.label}</span>
                  {/* Active indicator */}
                  {isActive && (
                    <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-gradient-to-r from-accent-red to-accent-orange rounded-full animate-scale-in" />
                  )}
                  {/* Hover indicator */}
                  <span className="absolute bottom-0 left-1/2 -translate-x-1/2 w-0 h-0.5 bg-border-light rounded-full transition-all duration-300 group-hover:w-1/2" />
                </>
              )}
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  );
}
