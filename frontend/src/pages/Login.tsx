/**
 * Login Page for Issue #41: Optional Authentication
 * 
 * Simple login form that authenticates with the backend
 * and stores the JWT token on success.
 */
import { useState, FormEvent } from 'react';
import { useAuth } from '../context/AuthContext';
import { Button } from '../components/common/Button';
import { ThemeToggle } from '../components/common/ThemeToggle';
import { useTheme } from '../hooks/useTheme';

export function Login() {
  const { login, isLoading, error, clearError } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [loginError, setLoginError] = useState<string | null>(null);

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    clearError();
    setLoginError(null);

    if (!username.trim() || !password.trim()) {
      setLoginError('Please enter both username and password');
      return;
    }

    const success = await login(username, password);
    if (!success) {
      setLoginError('Invalid username or password');
    }
    // On success, AuthContext will update isAuthenticated and App will redirect
  };

  return (
    <div className="min-h-screen bg-bg-primary flex items-center justify-center px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full">
        {/* Theme Toggle - positioned in top right */}
        <div className="fixed top-4 right-4">
          <ThemeToggle theme={theme} onToggle={toggleTheme} />
        </div>

        {/* Logo and Title */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-accent-red to-accent-orange flex items-center justify-center shadow-glow mx-auto mb-4">
            <svg 
              className="w-8 h-8 text-white" 
              fill="currentColor" 
              viewBox="0 0 20 20"
            >
              <path d="M10 18a8 8 0 100-16 8 8 0 000 16zM9.555 7.168A1 1 0 008 8v4a1 1 0 001.555.832l3-2a1 1 0 000-1.664l-3-2z" />
            </svg>
          </div>
          <h1 className="text-2xl font-bold text-text-primary">
            YouTube Watcher
          </h1>
          <p className="mt-2 text-text-secondary">
            Please sign in to continue
          </p>
        </div>

        {/* Login Form */}
        <div className="card p-6 sm:p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Username */}
            <div>
              <label 
                htmlFor="username" 
                className="block text-sm font-medium text-text-primary mb-2"
              >
                Username
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={isLoading}
                className="input w-full"
                placeholder="Enter username"
                autoComplete="username"
                autoFocus
              />
            </div>

            {/* Password */}
            <div>
              <label 
                htmlFor="password" 
                className="block text-sm font-medium text-text-primary mb-2"
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isLoading}
                className="input w-full"
                placeholder="Enter password"
                autoComplete="current-password"
              />
            </div>

            {/* Error Message */}
            {(error || loginError) && (
              <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
                {error || loginError}
              </div>
            )}

            {/* Submit Button */}
            <Button
              type="submit"
              variant="primary"
              size="lg"
              className="w-full"
              disabled={isLoading}
            >
              {isLoading ? (
                <span className="flex items-center justify-center gap-2">
                  <svg 
                    className="animate-spin h-5 w-5" 
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
                  Signing in...
                </span>
              ) : (
                'Sign In'
              )}
            </Button>
          </form>
        </div>

        {/* Footer */}
        <p className="mt-6 text-center text-sm text-text-tertiary">
          Protected instance · Contact administrator for access
        </p>
      </div>
    </div>
  );
}
