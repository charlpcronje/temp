// src/App.tsx
import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Providers
import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';

// Layouts
import DashboardLayout from './components/layouts/DashboardLayout';

// Pages
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import { LogsListPage, LogDetailPage } from './pages/LogsPage';
import UsersPage from './pages/UsersPage';
import SettingsPage from './pages/SettingsPage';
import SessionsPage from './pages/SessionsPage';
import WorkflowPage from './pages/WorkflowPage'; // Handles steps 1-9

// Auth components
import ProtectedRoute from './components/auth/ProtectedRoute';

// Upload component
import FileUpload from './components/upload/FileUpload'; // Import FileUpload

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <AuthProvider>
          <Router>
            <Routes>
              {/* Public routes */}
              <Route path="/login" element={<LoginPage />} />

              {/* Protected routes */}
              <Route element={<ProtectedRoute />}>
                <Route element={<DashboardLayout />}>
                  {/* Dashboard */}
                  <Route path="/" element={<Navigate to="/app/dashboard" replace />} />
                  <Route path="/app/dashboard" element={<DashboardPage />} />

                  {/* --- WORKFLOW ROUTES --- */}
                  {/* Dedicated Upload Route - Placed BEFORE the general workflow route */}
                  <Route path="/app/workflow/upload" element={<FileUpload />} />

                  {/* Main Workflow Route (handles steps 1-9 based on session param) */}
                  {/* This requires a session hash in the URL query params */}
                  <Route path="/app/workflow" element={<WorkflowPage />} />
                  {/* --- END WORKFLOW ROUTES --- */}


                  {/* Sessions */}
                  <Route path="/app/sessions" element={<SessionsPage />} />
                  <Route path="/app/sessions/:id" element={<LogDetailPage />} />

                  {/* Logs */}
                  <Route path="/app/logs" element={<LogsListPage />} />
                  <Route path="/app/logs/:id" element={<LogDetailPage />} />

                  {/* Settings */}
                  <Route path="/app/settings" element={<SettingsPage />} />

                  {/* Admin-only routes */}
                  <Route element={<ProtectedRoute requireAdmin={true} />}>
                      <Route path="/app/users" element={<UsersPage />} />
                  </Route>
                  {/* --- END Nested DashboardLayout Routes --- */}
                </Route>
                 {/* --- END Protected Routes --- */}
              </Route>

              {/* Fallback route */}
              <Route path="*" element={<Navigate to="/app/dashboard" replace />} />
            </Routes>
          </Router>
        </AuthProvider>
      </ThemeProvider>
    </QueryClientProvider>
  );
}

export default App;