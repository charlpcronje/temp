import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
// https://vitejs.dev/config/
export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src'),
        },
    },
    server: {
        // Proxy API requests to backend server during development
        proxy: {
            '/api': {
                target: 'http://localhost:8000',
                changeOrigin: true,
                rewrite: function (path) { return path.replace(/^\/api/, ''); },
            },
            // Proxy static file paths
            '/static': {
                target: 'http://localhost:8000',
                changeOrigin: true,
            },
        },
    },
    build: {
        // Output to the dist folder by default
        outDir: 'dist',
        // Generate source maps for debugging
        sourcemap: process.env.NODE_ENV !== 'production',
        // Minify the output in production
        minify: process.env.NODE_ENV === 'production',
        // Additional build options
        rollupOptions: {
            output: {
                manualChunks: {
                    vendor: ['react', 'react-dom', 'react-router-dom'],
                    ui: ['lucide-react', '@radix-ui/react-dialog', '@radix-ui/react-dropdown-menu'],
                },
            },
        },
    },
    // Handle environment variables
    envPrefix: 'VITE_',
});
