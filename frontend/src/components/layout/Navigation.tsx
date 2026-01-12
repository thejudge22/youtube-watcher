import { NavLink } from 'react-router-dom';

export function Navigation() {
  const navItems = [
    { to: '/', label: 'Inbox' },
    { to: '/saved', label: 'Saved' },
    { to: '/channels', label: 'Channels' },
  ];

  return (
    <nav className="bg-gray-800 border-b border-gray-700">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex space-x-8">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                `py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                  isActive
                    ? 'border-red-500 text-white'
                    : 'border-transparent text-gray-300 hover:text-white hover:border-gray-300'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </div>
      </div>
    </nav>
  );
}