// src/contexts/AuthContext.tsx
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { User } from "@/types";
import { authService } from "@/api/services";
import { checkAuth, getCurrentUser, setAuth, logout } from "@/api/client";
import config from "@/config";

interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  loading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType>({} as AuthContextType);

export const useAuth = () => useContext(AuthContext);

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(checkAuth());
  const [user, setUser] = useState<User | null>(getCurrentUser());
  const [loading, setLoading] = useState<boolean>(true);

  // For API key mode, we don't need to verify the token
  const isApiKeyMode = !config.auth.useJwtAuth && !!config.auth.apiKey;

  // Verify token on mount (only if using JWT auth)
  useEffect(() => {
    const verifyAuth = async () => {
      // Skip verification if using API key
      if (isApiKeyMode) {
        setIsAuthenticated(true);
        setLoading(false);
        return;
      }

      if (isAuthenticated) {
        try {
          const isValid = await authService.verifyToken();
          setIsAuthenticated(isValid);
          if (!isValid) {
            setUser(null);
            localStorage.removeItem(config.auth.tokenStorageKey);
            localStorage.removeItem(config.auth.userStorageKey);
          }
        } catch (error) {
          setIsAuthenticated(false);
          setUser(null);
          localStorage.removeItem(config.auth.tokenStorageKey);
          localStorage.removeItem(config.auth.userStorageKey);
        }
      }
      setLoading(false);
    };

    verifyAuth();
  }, [isAuthenticated, isApiKeyMode]);

  const login = async (username: string, password: string) => {
    // If using API key, simply set as authenticated
    if (isApiKeyMode) {
      setIsAuthenticated(true);
      setUser({
        id: 0,
        username: "API User",
        role: "admin" // Default to admin for API key mode
      });
      return;
    }

    setLoading(true);
    try {
      const data = await authService.login(username, password);
      setAuth(data);
      setIsAuthenticated(true);
      setUser(data.user);
    } catch (error) {
      console.error('Login failed:', error);
      throw error;
    } finally {
      setLoading(false);
    }
  };

  const logoutHandler = () => {
    logout();
    setIsAuthenticated(false);
    setUser(null);
  };

  return (
    <AuthContext.Provider
      value={{
        isAuthenticated,
        user,
        loading,
        login,
        logout: logoutHandler,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};