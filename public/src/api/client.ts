// src/api/client.ts

import axios from 'axios';
import { AuthResponse } from "@/types";
import config from "@/config";

// Create an axios instance with base URL
export const apiClient = axios.create({
  baseURL: config.api.baseURL,
  timeout: config.api.timeout,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add interceptor to inject auth token or API key
apiClient.interceptors.request.use((requestConfig) => {
  // If using JWT authentication (default)
  if (config.auth.useJwtAuth) {
    const token = localStorage.getItem(config.auth.tokenStorageKey);
    if (token) {
      requestConfig.headers['X-API-Key'] = token;
    }
  } 
  // If using API key authentication
  else if (config.auth.apiKey) {
    requestConfig.headers['X-API-Key'] = config.auth.apiKey;
  }
  
  return requestConfig;
});

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Handle session expiration or unauthorized access
    if (error.response && error.response.status === 401) {
      localStorage.removeItem(config.auth.tokenStorageKey);
      localStorage.removeItem(config.auth.userStorageKey);
      window.location.href = '/login';
    }
    
    // Log errors in development
    if (config.isDevelopment && config.features.enableLogging) {
      console.error('API Error:', error);
    }
    
    return Promise.reject(error);
  }
);

// Check if user is authenticated
export const checkAuth = (): boolean => {
  // If using JWT auth
  if (config.auth.useJwtAuth) {
    return !!localStorage.getItem(config.auth.tokenStorageKey);
  }
  // If using API key
  return !!config.auth.apiKey;
};

// Get current user from localStorage
export const getCurrentUser = () => {
  if (!config.auth.useJwtAuth) return null;
  
  const userJson = localStorage.getItem(config.auth.userStorageKey);
  return userJson ? JSON.parse(userJson) : null;
};

// Log out user
export const logout = () => {
  if (config.auth.useJwtAuth) {
    localStorage.removeItem(config.auth.tokenStorageKey);
    localStorage.removeItem(config.auth.userStorageKey);
  }
  window.location.href = '/login';
};

// Set authentication data
export const setAuth = (data: AuthResponse) => {
  if (config.auth.useJwtAuth) {
    localStorage.setItem(config.auth.tokenStorageKey, data.token);
    localStorage.setItem(config.auth.userStorageKey, JSON.stringify(data.user));
  }
};