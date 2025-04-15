/// <reference types="vite/client" />

/**
 * Central configuration for the Dashboard
 * Use this file to manage environment-specific settings
 */

// Load environment variables with fallbacks
const getEnvVar = (key: string, defaultValue: string = ''): string => {
    if (import.meta.env) {
        return import.meta.env[`VITE_${key}`] || defaultValue;
    }
    // @ts-ignore
    return process.env[`VITE_${key}`] || defaultValue;
};

// Configuration object
const config = {
    // API configuration
    api: {
        baseURL: getEnvVar('API_BASE_URL', 'http://localhost:8000'),
        timeout: parseInt(getEnvVar('API_TIMEOUT', '30000')),
    },

    // Authentication configuration
    auth: {
        tokenStorageKey: 'auth_token',
        userStorageKey: 'user',
        // If true, use JWT authentication. If false, use API key authentication
        useJwtAuth: getEnvVar('USE_JWT_AUTH', 'true') === 'true',
        // Used when useJwtAuth is false
        apiKey: getEnvVar('API_KEY', ''),
    },

    // File upload configuration
    upload: {
        maxFileSize: parseInt(getEnvVar('MAX_FILE_SIZE', '50000000')), // 50MB default
        acceptedFileTypes: getEnvVar('ACCEPTED_FILE_TYPES', '.csv,.xls,.xlsx'),
        chunkSize: parseInt(getEnvVar('UPLOAD_CHUNK_SIZE', '2000000')), // 2MB chunks
    },

    // UI configuration
    ui: {
        // Default theme (light or dark)
        defaultTheme: getEnvVar('DEFAULT_THEME', 'system'),
        // Sidebar collapsed by default on mobile
        sidebarCollapsedByDefault: getEnvVar('SIDEBAR_COLLAPSED', 'true') === 'true',
        // Dashboard refresh interval in ms (0 to disable auto-refresh)
        dashboardRefreshInterval: parseInt(getEnvVar('DASHBOARD_REFRESH', '0')),
    },

    // Feature flags
    features: {
        enableUserManagement: getEnvVar('ENABLE_USER_MANAGEMENT', 'true') === 'true',
        enableDarkMode: getEnvVar('ENABLE_DARK_MODE', 'true') === 'true',
        enableLogging: getEnvVar('ENABLE_LOGGING', 'true') === 'true',
    },

    // Environment
    environment: getEnvVar('NODE_ENV', 'development'),
    isProduction: getEnvVar('NODE_ENV', 'development') === 'production',
    isDevelopment: getEnvVar('NODE_ENV', 'development') === 'development',
};

export default config;