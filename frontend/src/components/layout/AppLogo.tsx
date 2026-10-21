import { Link } from 'react-router-dom';
import { PlayIcon } from '@heroicons/react/24/solid';

export function AppLogo() {
  return (
    <Link to="/" className="flex items-center gap-2.5 hover:opacity-90 transition-opacity">
      <span className="w-7 h-7 rounded-lg bg-accent-red flex items-center justify-center">
        <PlayIcon className="w-4 h-4 text-white" />
      </span>
      <span className="text-base font-semibold text-text-primary tracking-tight">
        YouTube Watcher
      </span>
    </Link>
  );
}
