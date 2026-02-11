/**
 * Authentication Context for Issue #41: Optional Authentication
 * 
 * Manages authentication state including:
 * - Checking if auth is enabled on the backend
 * - Storing and validating JWT tokens
 * - Login/logout functionality
 * - Automatic token storage in localStorage
 */
import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  type ReactNode,
} from 'react';
import { authApi, setAuthToken, clearAuthToken } from '../api/client';

interface AuthState {
  /** Whether authentication is enabled on the backend */
  isAuthEnabled: boolean;
  /** Whether the user is currently authenticated (has valid token) */
  isAuthenticated: boolean;
  /** Whether auth state is still being determined */
  isLoading: boolean;
  /** Error message from last auth operation */
  error: string | null;
}

interface AuthContextType extends AuthState {
  /** Log in with username and password */
  login: (username: string, password: string) => Promise<boolean>;
  /** Log out and clear stored token */
  logout: () => void;
  /** Clear any error message */
  clearError: () => void;
}

const AuthContext = createContext<AuthContextType | null>(null);

const STORAGE_KEY = 'youtube_watcher_token';

interface AuthProviderProps {
  children: ReactNode;
}

export function AuthProvider({ children }: AuthProviderProps) {
  const [state, setState] = useState<AuthState>({
    isAuthEnabled: false,
    isAuthenticated: false,
    isLoading: true,
    error: null,
  });

  /**
   * Check if auth is enabled on the backend and validate any stored token
   */
  const initializeAuth = useCallback(async () => {
    try {
      // First check if auth is enabled
      const statusResponse = await authApi.getStatus();
      const isAuthEnabled = statusResponse.data.enabled;

      if (!isAuthEnabled) {
        // Auth is disabled, no login needed
        setState({
          isAuthEnabled: false,
          isAuthenticated: true, // Consider authenticated since no auth needed
          isLoading: false,
          error: null,
        });
        return;
      }

      // Auth is enabled, check for stored token
      const storedToken = localStorage.getItem(STORAGE_KEY);
      
      if (!storedToken) {
        // No token stored, need to login
        setState({
          isAuthEnabled: true,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        });
        return;
      }

      // Validate the stored token
      try {
        const verifyResponse = await authApi.verifyToken(storedToken);
        if (verifyResponse.data.valid) {
          // Token is valid
          setAuthToken(storedToken);
          setState({
            isAuthEnabled: true,
            isAuthenticated: true,
            isLoading: false,
            error: null,
          });
        } else {
          // Token is invalid, remove it
          localStorage.removeItem(STORAGE_KEY);
          setState({
            isAuthEnabled: true,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        }
      } catch {
        // Token validation failed, remove it
        localStorage.removeItem(STORAGE_KEY);
        setState({
          isAuthEnabled: true,
          isAuthenticated: false,
          isLoading: false,
          error: null,
        });
      }
    } catch (err) {
      // Failed to check auth status, assume auth is disabled to allow access
      setState({
        isAuthEnabled: false,
        isAuthenticated: true,
        isLoading: false,
        error: 'Failed to check authentication status',
      });
    }
  }, []);

  // Initialize auth on mount
  useEffect(() => {
    initializeAuth();
  }, [initializeAuth]);

  /**
   * Log in with username and password
   */
  const login = useCallback(async (username: string, password: string): Promise<boolean> => {
    setState(prev => ({ ...prev, isLoading: true, error: null }));

    try {
      const response = await authApi.login(username, password);
      const { token } = response.data;

      // Store token and update state
      localStorage.setItem(STORAGE_KEY, token);
      setAuthToken(token);
      setState({
        isAuthEnabled: true,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });
      return true;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Login failed';
      setState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
      }));
      return false;
    }
  }, []);

  /**
   * Log out and clear stored token
   */
  const logout = useCallback(() => {
    // Call logout endpoint (best effort)
    authApi.logout().catch(() => {
      // Ignore errors on logout
    });

    // Clear token from storage and API client
    localStorage.removeItem(STORAGE_KEY);
    clearAuthToken();

    // Reset state
    setState({
      isAuthEnabled: true,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });
  }, []);

  /**
   * Clear error message
   */
  const clearError = useCallback(() => {
    setState(prev => ({ ...prev, error: null }));
  }, []);

  const value: AuthContextType = {
    ...state,
    login,
    logout,
    clearError,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Hook to access authentication context
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
