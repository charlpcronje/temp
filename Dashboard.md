# Combined Project Files

## C:\xampp\htdocs\DocTypeGen\public\src\api\client.ts
```ts
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
```

## C:\xampp\htdocs\DocTypeGen\public\src\api\services.ts
```ts
// src/api/services.ts
import { apiClient } from './client';
import { 
  AuthResponse, 
  SessionStatus, 
  CommandResponse,
  ValidationResult,
  MappingResult,
  HtmlGenerationResult,
  PdfGenerationResult,
  User,
  LogDirectory,
  LogInfo,
  LookupResolutionResult,
  LookupException,
  LookupExceptionsList,
  ExceptionResolutionRequest,
  ExceptionResolutionResult,
  Entity,
  EntityCreationResult,
  EntitiesForCreationResult
} from "@/types";

// Auth service
export const authService = {
  login: async (username: string, password: string): Promise<AuthResponse> => {
    const response = await apiClient.post<AuthResponse>('/api/auth/login', { username, password });
    return response.data;
  },
  
  verifyToken: async (): Promise<boolean> => {
    try {
      const response = await apiClient.get('/api/auth/verify');
      return response.data.valid === true;
    } catch (error) {
      return false;
    }
  }
};

// Command service
export const commandService = {
  getCommands: async (): Promise<Record<string, any>> => {
    const response = await apiClient.get('/api/commands');
    return response.data;
  },
  
  getStatus: async (): Promise<SessionStatus> => {
    const response = await apiClient.get<SessionStatus>('/api/status');
    return response.data;
  },
  
  importFile: async (filePath: string): Promise<CommandResponse> => {
    const formData = new FormData();
    formData.append('file_path', filePath);
    
    const response = await apiClient.post<CommandResponse>('/api/run/import', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    });
    return response.data;
  },
  
  uploadFile: async (file: File): Promise<CommandResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await apiClient.post<CommandResponse>('/api/run/import-upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
    return response.data;
  },
  
  runCommand: async (command: string, args: Record<string, any> = {}): Promise<CommandResponse> => {
    const response = await apiClient.post<CommandResponse>(`/api/run/command`, { command, args });
    return response.data;
  },
  
  validateData: async (): Promise<ValidationResult> => {
    const response = await apiClient.post<CommandResponse>('/api/run/validate');
    return response.data.result;
  },
  
  generateMapping: async (): Promise<MappingResult> => {
    const response = await apiClient.post<CommandResponse>('/api/run/map');
    return response.data.result;
  },
  
  deleteMapping: async (): Promise<CommandResponse> => {
    const response = await apiClient.post<CommandResponse>('/api/run/delete_mapping');
    return response.data;
  },
  
  updateMapping: async (fieldUpdates: Record<string, any>): Promise<MappingResult> => {
    const response = await apiClient.post<CommandResponse>('/api/run/map', { field_updates: fieldUpdates });
    return response.data.result;
  },
  
  generateHtml: async (): Promise<HtmlGenerationResult> => {
    const response = await apiClient.post<CommandResponse>('/api/run/html');
    return response.data.result;
  },
  
  generatePdf: async (): Promise<PdfGenerationResult> => {
    const response = await apiClient.post<CommandResponse>('/api/run/pdf');
    return response.data.result;
  },
  
  resolveLookups: async (): Promise<LookupResolutionResult> => {
    const response = await apiClient.post<CommandResponse>('/api/run/lookup');
    return response.data.result;
  },
  
  getLookupExceptions: async (status?: string, lookupType?: string): Promise<LookupExceptionsList> => {
    const params = new URLSearchParams();
    if (status) params.append('status', status);
    if (lookupType) params.append('type', lookupType);
    
    const response = await apiClient.get<LookupExceptionsList>('/api/lookups/exceptions', { params });
    return response.data;
  },
  
  resolveLookupException: async (
    exceptionId: number, 
    resolution: ExceptionResolutionRequest
  ): Promise<ExceptionResolutionResult> => {
    const response = await apiClient.post<ExceptionResolutionResult>(
      `/api/lookups/exceptions/${exceptionId}/resolve`, 
      resolution
    );
    return response.data;
  },
  
  getEntitiesForCreation: async (): Promise<EntitiesForCreationResult> => {
    const response = await apiClient.get<EntitiesForCreationResult>('/api/lookups/entities-for-creation');
    return response.data;
  },
  
  createEntity: async (entity: Entity): Promise<EntityCreationResult> => {
    const response = await apiClient.post<EntityCreationResult>('/api/entities/create', entity);
    return response.data;
  },
  
  syncToTenantDb: async (): Promise<CommandResponse> => {
    const response = await apiClient.post<CommandResponse>('/api/run/command', {
      command: 'sync_tenant_db',
      args: {}
    });
    return response.data;
  },
  
  transferToS3: async (): Promise<CommandResponse> => {
    const response = await apiClient.post<CommandResponse>('/api/run/command', {
      command: 'transfer_to_s3',
      args: {}
    });
    return response.data;
  }
};

// Session service
export const sessionService = {
  getLogs: async (): Promise<LogDirectory[]> => {
    const response = await apiClient.get<LogDirectory[]>('/api/logs');
    return response.data;
  },
  
  getLogInfo: async (hash: string): Promise<LogInfo> => {
    const response = await apiClient.get<LogInfo>(`/api/logs/${hash}`);
    return response.data;
  },
  
  renameLog: async (hash: string, name: string): Promise<void> => {
    await apiClient.post(`/api/logs/${hash}/rename`, { name });
  }
};

// User service
export const userService = {
  getUsers: async (): Promise<User[]> => {
    const response = await apiClient.get<User[]>('/api/users');
    return response.data;
  },
  
  createUser: async (username: string, password: string, role: string): Promise<void> => {
    await apiClient.post('/api/users', { username, password, role });
  },
  
  updateUser: async (id: number, data: Partial<User & { password?: string }>): Promise<void> => {
    await apiClient.put(`/api/users/${id}`, data);
  },
  
  deleteUser: async (id: number): Promise<void> => {
    await apiClient.delete(`/api/users/${id}`);
  }
};
```

## C:\xampp\htdocs\DocTypeGen\public\src\App.tsx
```tsx
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
import WorkflowPage from './pages/WorkflowPage';

// Auth components
import ProtectedRoute from './components/auth/ProtectedRoute';

// Upload components
import FileUpload from './components/upload/FileUpload';

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
                  
                  {/* Workflow */}
                  <Route path="/app/workflow" element={<WorkflowPage />} />
                  <Route path="/app/workflow/upload" element={<WorkflowPage />} />
                  
                  {/* Sessions */}
                  <Route path="/app/sessions" element={<SessionsPage />} />
                  <Route path="/app/sessions/:id" element={<LogDetailPage />} />
                  
                  {/* Logs */}
                  <Route path="/app/logs" element={<LogsListPage />} />
                  <Route path="/app/logs/:id" element={<LogDetailPage />} />
                  
                  {/* Settings */}
                  <Route path="/app/settings" element={<SettingsPage />} />
                </Route>
                
                {/* Admin-only routes */}
                <Route element={<ProtectedRoute requireAdmin={true} />}>
                  <Route element={<DashboardLayout />}>
                    <Route path="/app/users" element={<UsersPage />} />
                  </Route>
                </Route>
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
```

## C:\xampp\htdocs\DocTypeGen\public\src\components\auth\ProtectedRoute.tsx
```tsx
// src/components/auth/ProtectedRoute.tsx
import React from 'react';
import { Navigate, Outlet } from 'react-router-dom';
import { useAuth } from "@/contexts/AuthContext";
import { Spinner } from '../ui/spinner';

interface ProtectedRouteProps {
  requireAdmin?: boolean;
}

const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ requireAdmin = false }) => {
  const { isAuthenticated, user, loading } = useAuth();

  // Show loading spinner while checking authentication
  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  // Redirect to login if not authenticated
  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  // Redirect to dashboard if admin access is required but user is not admin
  if (requireAdmin && user?.role !== 'admin') {
    return <Navigate to="/" replace />;
  }

  // Render children if authenticated and has required role
  return <Outlet />;
};

export default ProtectedRoute;
```

## C:\xampp\htdocs\DocTypeGen\public\src\components\layouts\DashboardLayout.tsx
```tsx
// src/components/layouts/DashboardLayout.tsx
import React, { useState, useEffect } from 'react';
import { Outlet } from 'react-router-dom';
import { cn } from "@/lib/utils";
import Header from './Header';
import Sidebar from './Sidebar';

const DashboardLayout: React.FC = () => {
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth < 768);

  const toggleSidebar = () => {
    setIsSidebarOpen(!isSidebarOpen);
  };

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth < 768);
      if (window.innerWidth >= 768) {
        setIsSidebarOpen(false);
      }
    };

    window.addEventListener('resize', handleResize);
    
    return () => {
      window.removeEventListener('resize', handleResize);
    };
  }, []);

  return (
    <div className="min-h-screen bg-background">
      <Header toggleSidebar={toggleSidebar} />
      
      <div className="flex">
        <Sidebar
          isMobile={isMobile}
          isSidebarOpen={isSidebarOpen}
          toggleSidebar={toggleSidebar}
        />
        
        <main
          className={cn(
            "flex-1 p-4 sm:p-6 md:p-8",
            !isMobile && "md:ml-64"
          )}
        >
          <Outlet />
        </main>
      </div>
      
      {/* Backdrop for mobile sidebar */}
      {isMobile && isSidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-background/80 backdrop-blur-sm"
          onClick={toggleSidebar}
        />
      )}
    </div>
  );
};

export default DashboardLayout;
```

## C:\xampp\htdocs\DocTypeGen\public\src\components\layouts\Header.tsx
```tsx
// src/components/layouts/Header.tsx
import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Menu, LogOut, Sun, Moon, User } from 'lucide-react';
import { Button } from '../ui/button';
import { useAuth } from "@/contexts/AuthContext";
import { useTheme } from "@/contexts/ThemeContext";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';

interface HeaderProps {
  toggleSidebar: () => void;
}

const Header: React.FC<HeaderProps> = ({ toggleSidebar }) => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-4 border-b bg-background px-4 sm:px-6 lg:px-8">
      <Button 
        variant="ghost" 
        size="icon" 
        className="md:hidden" 
        onClick={toggleSidebar}
      >
        <Menu className="h-5 w-5" />
        <span className="sr-only">Toggle sidebar</span>
      </Button>
      
      <div className="ml-auto flex items-center gap-4">
        <Button 
          variant="ghost" 
          size="icon" 
          onClick={toggleTheme}
          className="text-muted-foreground hover:text-foreground"
        >
          {theme === 'light' ? (
            <Moon className="h-5 w-5" />
          ) : (
            <Sun className="h-5 w-5" />
          )}
          <span className="sr-only">Toggle theme</span>
        </Button>
        
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="ghost" size="icon" className="rounded-full">
              <Avatar className="h-8 w-8">
                <AvatarFallback className="bg-primary text-primary-foreground">
                  {user?.username.substring(0, 2).toUpperCase() || 'U'}
                </AvatarFallback>
              </Avatar>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end" className="w-56">
            <div className="flex flex-col space-y-1 p-2">
              <p className="text-sm font-medium leading-none">{user?.username}</p>
              <p className="text-xs leading-none text-muted-foreground">
              {(user?.username || '').substring(0, 2).toUpperCase() || 'U'}
              </p>
            </div>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => navigate('/settings')} className="cursor-pointer">
              <User className="mr-2 h-4 w-4" />
              <span>Profile</span>
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={logout} className="cursor-pointer text-destructive focus:text-destructive">
              <LogOut className="mr-2 h-4 w-4" />
              <span>Logout</span>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </header>
  );
};

export default Header;
```

## C:\xampp\htdocs\DocTypeGen\public\src\components\layouts\Sidebar.tsx
```tsx
// src/components/layouts/Sidebar.tsx
import React from 'react';
import { NavLink } from 'react-router-dom';
import { 
  LayoutDashboard, 
  FileInput, 
  Workflow, 
  File, 
  FileText, 
  Users, 
  Settings,
  Menu,
  X
} from 'lucide-react';
import { cn } from "@/lib/utils";
import { useAuth } from "@/contexts/AuthContext";
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';

interface SidebarProps {
  isMobile: boolean;
  isSidebarOpen: boolean;
  toggleSidebar: () => void;
}

const Sidebar: React.FC<SidebarProps> = ({ 
  isMobile, 
  isSidebarOpen, 
  toggleSidebar 
}) => {
  const { user } = useAuth();
  const isAdmin = user?.role === 'admin';

  const navItems = [
    { name: 'Dashboard', path: '/', icon: LayoutDashboard },
    { name: 'Sessions', path: '/sessions', icon: FileInput },
    { name: 'Workflow', path: '/workflow', icon: Workflow },
    { name: 'Logs', path: '/logs', icon: FileText },
    ...(isAdmin ? [{ name: 'Users', path: '/users', icon: Users }] : []),
    { name: 'Settings', path: '/settings', icon: Settings },
  ];

  if (isMobile && !isSidebarOpen) return null;

  return (
    <div 
      className={cn(
        "fixed inset-y-0 left-0 z-50 w-64 bg-background border-r transition-transform duration-300 ease-in-out",
        isMobile && !isSidebarOpen && "-translate-x-full",
      )}
    >
      <div className="flex h-14 items-center px-4 border-b">
        <h2 className="text-lg font-semibold">DocTypeGen</h2>
        {isMobile && (
          <Button 
            variant="ghost" 
            size="icon" 
            className="ml-auto" 
            onClick={toggleSidebar}
          >
            <X className="h-4 w-4" />
          </Button>
        )}
      </div>
      <ScrollArea className="h-[calc(100vh-3.5rem)]">
        <div className="px-3 py-2">
          <nav className="flex flex-col gap-1">
            {navItems.map((item) => (
              <NavLink
                key={item.path}
                to={item.path}
                end={item.path === '/'}
                className={({ isActive }) =>
                  cn(
                    "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium",
                    "transition-colors hover:bg-accent hover:text-accent-foreground",
                    isActive ? "bg-accent text-accent-foreground" : "transparent"
                  )
                }
                onClick={isMobile ? toggleSidebar : undefined}
              >
                <item.icon className="h-4 w-4" />
                <span>{item.name}</span>
              </NavLink>
            ))}
          </nav>
        </div>
      </ScrollArea>
    </div>
  );
};

export default Sidebar;
```

## C:\xampp\htdocs\DocTypeGen\public\src\components\lookup\DocumentsTable.tsx
```tsx
// src/components/lookup/DocumentsTable.tsx
import React from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Eye } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface Document {
  id: number;
  document_id: number;
  input_file: string;
  row: number;
  lookup_type: string;
  lookup_field: string;
  lookup_value: string;
  lookup_match?: string | null;
  status: string;
  [key: string]: any; // For other dynamic fields
}

interface DocumentsTableProps {
  documents: Document[];
}

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const statusMap: Record<string, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
    'pending': { label: 'Pending', variant: 'outline' },
    'matched': { label: 'Matched', variant: 'default' },
    'exception': { label: 'Exception', variant: 'destructive' },
    'accepted': { label: 'Accepted', variant: 'default' },
    'rejected': { label: 'Rejected', variant: 'destructive' },
    'for_creation': { label: 'For Creation', variant: 'secondary' },
  };

  const { label, variant } = statusMap[status] || { label: status, variant: 'outline' };

  return <Badge variant={variant}>{label}</Badge>;
};

const DocumentsTable: React.FC<DocumentsTableProps> = ({ documents }) => {
  if (!documents || documents.length === 0) {
    return <div className="text-center py-8 text-muted-foreground">No documents found.</div>;
  }

  return (
    <div className="border rounded-md overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12">ID</TableHead>
            <TableHead>Input File</TableHead>
            <TableHead>Row</TableHead>
            <TableHead>Lookup Type</TableHead>
            <TableHead>Lookup Value</TableHead>
            <TableHead>Match</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="w-12">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {documents.map((doc) => (
            <TableRow key={doc.id}>
              <TableCell className="font-medium">{doc.document_id || doc.id}</TableCell>
              <TableCell className="max-w-[180px] truncate" title={doc.input_file}>
                {doc.input_file ? doc.input_file.split('/').pop() : '-'}
              </TableCell>
              <TableCell>{doc.row}</TableCell>
              <TableCell>{doc.lookup_type}</TableCell>
              <TableCell className="max-w-[180px] truncate" title={doc.lookup_value}>
                {doc.lookup_value}
              </TableCell>
              <TableCell className="max-w-[180px] truncate" title={doc.lookup_match || ''}>
                {doc.lookup_match || '-'}
              </TableCell>
              <TableCell>
                <StatusBadge status={doc.status} />
              </TableCell>
              <TableCell>
                <Button variant="ghost" size="icon" title="View Document">
                  <Eye className="h-4 w-4" />
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};

export default DocumentsTable;

```

## C:\xampp\htdocs\DocTypeGen\public\src\components\lookup\ExceptionsTable.tsx
```tsx
// src/components/lookup/ExceptionsTable.tsx
import React from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { AlertTriangle, Wrench } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { LookupException } from '@/types';

interface ExceptionsTableProps {
  exceptions: LookupException[];
  onResolve: (exceptionId: number) => void;
}

const StatusBadge: React.FC<{ status: string }> = ({ status }) => {
  const statusMap: Record<string, { label: string; variant: "default" | "secondary" | "destructive" | "outline" }> = {
    'pending': { label: 'Pending', variant: 'outline' },
    'accepted': { label: 'Accepted', variant: 'default' },
    'rejected': { label: 'Rejected', variant: 'destructive' },
    'for_creation': { label: 'For Creation', variant: 'secondary' },
  };

  const { label, variant } = statusMap[status] || { label: status, variant: 'outline' };

  return <Badge variant={variant}>{label}</Badge>;
};

const ExceptionsTable: React.FC<ExceptionsTableProps> = ({ exceptions, onResolve }) => {
  if (!exceptions || exceptions.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <AlertTriangle className="inline-block mb-2 h-8 w-8 text-amber-500" />
        <p>No exceptions to resolve.</p>
      </div>
    );
  }

  return (
    <div className="border rounded-md overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead className="w-12">ID</TableHead>
            <TableHead>Input File</TableHead>
            <TableHead>Row</TableHead>
            <TableHead>Lookup Type</TableHead>
            <TableHead>Lookup Value</TableHead>
            <TableHead>Exception</TableHead>
            <TableHead>Status</TableHead>
            <TableHead className="w-[100px]">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {exceptions.map((exception) => (
            <TableRow key={exception.id}>
              <TableCell className="font-medium">{exception.id}</TableCell>
              <TableCell className="max-w-[180px] truncate" title={exception.input_file}>
                {exception.input_file ? exception.input_file.split('/').pop() : '-'}
              </TableCell>
              <TableCell>{exception.row}</TableCell>
              <TableCell>{exception.lookup_type}</TableCell>
              <TableCell className="max-w-[180px] truncate" title={exception.lookup_value}>
                {exception.lookup_value}
              </TableCell>
              <TableCell className="max-w-[200px] truncate" title={exception.exception_message}>
                {exception.exception_message}
              </TableCell>
              <TableCell>
                <StatusBadge status={exception.status} />
              </TableCell>
              <TableCell>
                <Button 
                  onClick={() => onResolve(exception.id)}
                  variant="outline" 
                  size="sm" 
                  className="h-8 px-2 flex items-center"
                >
                  <Wrench className="mr-1 h-3 w-3" />
                  Resolve
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};

export default ExceptionsTable;

```

## C:\xampp\htdocs\DocTypeGen\public\src\components\lookup\ForCreationTable.tsx
```tsx
// src/components/lookup/ForCreationTable.tsx
import React from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Plus } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { LookupException } from '@/types';

interface ForCreationTableProps {
  documents: LookupException[];
}

const ForCreationTable: React.FC<ForCreationTableProps> = ({ documents }) => {
  if (!documents || documents.length === 0) {
    return (
      <div className="text-center py-8 text-muted-foreground">
        <Plus className="inline-block mb-2 h-8 w-8 text-blue-500" />
        <p>No documents marked for entity creation.</p>
      </div>
    );
  }

  // Group documents by lookup type and value for more efficient display
  const groupedDocuments = documents.reduce((acc, doc) => {
    const key = `${doc.lookup_type}:${doc.lookup_value}`;
    if (!acc[key]) {
      acc[key] = {
        lookup_type: doc.lookup_type,
        lookup_value: doc.lookup_value,
        count: 0,
        documents: []
      };
    }
    acc[key].count += 1;
    acc[key].documents.push(doc);
    return acc;
  }, {} as Record<string, { lookup_type: string; lookup_value: string; count: number; documents: LookupException[] }>);

  return (
    <div className="border rounded-md overflow-hidden">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Entity Type</TableHead>
            <TableHead>Value</TableHead>
            <TableHead className="w-24">Count</TableHead>
            <TableHead className="w-[180px]">Sample Data</TableHead>
            <TableHead className="w-[100px]">Actions</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {Object.values(groupedDocuments).map((group, index) => (
            <TableRow key={index}>
              <TableCell className="font-medium">{group.lookup_type}</TableCell>
              <TableCell className="max-w-[180px] truncate" title={group.lookup_value}>
                {group.lookup_value}
              </TableCell>
              <TableCell>
                <Badge variant="secondary">{group.count}</Badge>
              </TableCell>
              <TableCell>
                {group.documents[0] && (
                  <div className="max-w-[180px] max-h-[100px] overflow-auto text-xs">
                    <pre className="whitespace-pre-wrap">
                      {JSON.stringify(
                        Object.fromEntries(
                          Object.entries(group.documents[0].data).slice(0, 3)
                        ), 
                        null, 
                        1
                      )}
                      {Object.keys(group.documents[0].data).length > 3 && '...'}
                    </pre>
                  </div>
                )}
              </TableCell>
              <TableCell>
                <Button 
                  variant="outline" 
                  size="sm" 
                  className="h-8 px-2 flex items-center"
                >
                  <Plus className="mr-1 h-3 w-3" />
                  Create
                </Button>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  );
};

export default ForCreationTable;

```

## C:\xampp\htdocs\DocTypeGen\public\src\components\lookup\LookupExceptionResolver.tsx
```tsx
// src/components/lookup/LookupExceptionResolver.tsx
import React, { useState, useEffect, useCallback } from 'react';
import { commandService } from '@/api/services';
import { LookupException, ExceptionResolutionRequest } from '@/types';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { RadioGroup, RadioGroupItem } from '@/components/ui/radio-group';
import { Checkbox } from '@/components/ui/checkbox';
import { Spinner } from '@/components/ui/spinner';
import { Badge } from '@/components/ui/badge';
import { ArrowLeft, ArrowRight, CheckCircle, XCircle, Plus, Info, ChevronDown, ChevronUp, AlertTriangle } from 'lucide-react';
import { toast } from '@/components/ui/use-toast';

interface LookupExceptionResolverProps {
  isOpen: boolean;
  onClose: () => void;
  exceptionId: number | null;
  onResolved: () => void;
}

const KeyboardShortcutHelp: React.FC = () => (
  <div className="text-xs text-muted-foreground mt-4 border-t pt-2">
    <h4 className="font-medium mb-1">Keyboard Shortcuts:</h4>
    <div className="grid grid-cols-2 gap-1">
      <div className="flex items-center">
        <kbd className="px-1 bg-muted rounded text-xs">a</kbd>
        <span className="ml-1">Accept with value</span>
      </div>
      <div className="flex items-center">
        <kbd className="px-1 bg-muted rounded text-xs">r</kbd>
        <span className="ml-1">Reject exception</span>
      </div>
      <div className="flex items-center">
        <kbd className="px-1 bg-muted rounded text-xs">c</kbd>
        <span className="ml-1">Mark for creation</span>
      </div>
      <div className="flex items-center">
        <kbd className="px-1 bg-muted rounded text-xs">&#8592;</kbd>
        <span className="ml-1">Previous exception</span>
      </div>
      <div className="flex items-center">
        <kbd className="px-1 bg-muted rounded text-xs">&#8594;</kbd>
        <span className="ml-1">Next exception</span>
      </div>
      <div className="flex items-center">
        <kbd className="px-1 bg-muted rounded text-xs">b</kbd>
        <span className="ml-1">Apply to similar</span>
      </div>
    </div>
  </div>
);

const LookupExceptionResolver: React.FC<LookupExceptionResolverProps> = ({ 
  isOpen, 
  onClose, 
  exceptionId,
  onResolved 
}) => {
  const [exceptions, setExceptions] = useState<LookupException[]>([]);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  const [isResolving, setIsResolving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Resolution form state
  const [resolutionAction, setResolutionAction] = useState<'accept' | 'reject' | 'for_creation'>('accept');
  const [lookupValue, setLookupValue] = useState('');
  const [applyToSimilar, setApplyToSimilar] = useState(false);
  const [similarityOptions, setSimilarityOptions] = useState({
    lookup_type: true,
    lookup_field: true,
    exception_message: false
  });
  
  // Load exceptions on initial open
  useEffect(() => {
    if (isOpen) {
      loadExceptions();
    }
  }, [isOpen]);
  
  // Set current exception when exceptionId changes
  useEffect(() => {
    if (exceptionId && exceptions.length > 0) {
      const index = exceptions.findIndex(e => e.id === exceptionId);
      if (index !== -1) {
        setCurrentIndex(index);
      }
    }
  }, [exceptionId, exceptions]);
  
  // Reset form when current exception changes
  useEffect(() => {
    if (exceptions.length > 0) {
      const currentException = exceptions[currentIndex];
      setLookupValue(currentException.lookup_value || '');
      setResolutionAction('accept');
      setApplyToSimilar(false);
      
      // If we have potential matches, pre-populate with the first one
      if (currentException.potential_matches?.length) {
        setLookupValue(String(currentException.potential_matches[0].display));
      }
    }
  }, [currentIndex, exceptions]);
  
  const loadExceptions = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Only get pending exceptions
      const result = await commandService.getLookupExceptions('pending');
      setExceptions(result.exceptions || []);
      
      if (result.exceptions.length === 0) {
        setError('No pending exceptions to resolve');
      }
    } catch (err: any) {
      console.error('Error loading exceptions:', err);
      setError(err.message || 'Failed to load exceptions');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleNext = () => {
    if (currentIndex < exceptions.length - 1) {
      setCurrentIndex(currentIndex + 1);
    }
  };
  
  const handlePrevious = () => {
    if (currentIndex > 0) {
      setCurrentIndex(currentIndex - 1);
    }
  };
  
  const handleResolve = async () => {
    if (exceptions.length === 0) return;
    
    const currentException = exceptions[currentIndex];
    setIsResolving(true);
    setError(null);
    
    const resolution: ExceptionResolutionRequest = {
      accept: resolutionAction === 'accept',
      mark_for_creation: resolutionAction === 'for_creation',
      lookup_value: resolutionAction === 'accept' ? lookupValue : undefined,
      apply_to_similar: applyToSimilar,
      similarity_criteria: applyToSimilar ? similarityOptions : undefined
    };
    
    try {
      const result = await commandService.resolveLookupException(currentException.id, resolution);
      
      if (result.status === 'success') {
        // Update the local state to remove resolved exceptions
        setExceptions(prev => prev.filter(e => e.id !== currentException.id));
        
        // Show success message with count if batch resolved
        if (result.affected_count > 1) {
          toast({
            title: 'Exceptions Resolved',
            description: `Successfully resolved ${result.affected_count} similar exceptions`,
            duration: 3000
          });
        } else {
          toast({
            title: 'Exception Resolved',
            description: 'Successfully resolved the exception',
            duration: 2000
          });
        }
        
        // Notify parent component
        onResolved();
        
        // Move to next exception or close if done
        if (currentIndex >= exceptions.length - 1) {
          if (exceptions.length <= 1) {
            // If this was the last exception, close the dialog
            onClose();
          } else {
            // Otherwise, set the index to the new last item
            setCurrentIndex(exceptions.length - 2);
          }
        }
      } else {
        setError(result.message);
      }
    } catch (err: any) {
      console.error('Error resolving exception:', err);
      setError(err.message || 'Failed to resolve exception');
    } finally {
      setIsResolving(false);
    }
  };
  
  // Keyboard shortcut handler
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (!isOpen) return;
    
    // Don't trigger shortcuts when typing in input fields
    if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
      return;
    }
    
    switch (e.key) {
      case 'ArrowRight':
        handleNext();
        break;
      case 'ArrowLeft':
        handlePrevious();
        break;
      case 'a':
        setResolutionAction('accept');
        // Focus the input field
        document.getElementById('lookup-value')?.focus();
        break;
      case 'r':
        setResolutionAction('reject');
        handleResolve();
        break;
      case 'c':
        setResolutionAction('for_creation');
        handleResolve();
        break;
      case 'b':
        setApplyToSimilar(!applyToSimilar);
        break;
      default:
        break;
    }
  }, [isOpen, handleNext, handlePrevious, resolutionAction, applyToSimilar, handleResolve]);
  
  // Set up keyboard shortcuts
  useEffect(() => {
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);
  
  const currentException = exceptions[currentIndex];
  
  return (
    <Dialog open={isOpen} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-4xl h-[80vh] flex flex-col">
        <DialogHeader>
          <DialogTitle>
            Exception Resolution {exceptions.length > 0 && `(${currentIndex + 1}/${exceptions.length})`}
          </DialogTitle>
          <DialogDescription>
            Resolve lookup exceptions quickly with the tools below
          </DialogDescription>
        </DialogHeader>
        
        {isLoading ? (
          <div className="flex-1 flex items-center justify-center">
            <Spinner size="lg" />
            <span className="ml-2">Loading exceptions...</span>
          </div>
        ) : error && exceptions.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center">
            <AlertTriangle className="h-12 w-12 text-amber-500 mb-4" />
            <h3 className="text-lg font-medium mb-2">No Exceptions to Resolve</h3>
            <p className="text-muted-foreground mb-6">{error}</p>
            <Button onClick={onClose}>Close</Button>
          </div>
        ) : exceptions.length === 0 ? (
          <div className="flex-1 flex flex-col items-center justify-center text-center">
            <CheckCircle className="h-12 w-12 text-green-500 mb-4" />
            <h3 className="text-lg font-medium mb-2">All Exceptions Resolved</h3>
            <p className="text-muted-foreground mb-6">Great job! There are no more exceptions to resolve.</p>
            <Button onClick={onClose}>Close</Button>
          </div>
        ) : (
          <>
            {/* Main content: split view */}
            <div className="flex-1 flex flex-col md:flex-row gap-4 overflow-hidden">
              {/* Left panel: Document data */}
              <div className="w-full md:w-1/2 bg-muted/30 rounded-md p-4 overflow-y-auto">
                <h3 className="text-sm font-medium mb-2">Document Data</h3>
                <div className="space-y-2">
                  {currentException && Object.entries(currentException.data || {}).map(([key, value]) => (
                    <div key={key} className="grid grid-cols-2 text-sm">
                      <span className="font-medium">{key}</span>
                      <span>{String(value)}</span>
                    </div>
                  ))}
                </div>
              </div>
              
              {/* Right panel: Resolution options */}
              <div className="w-full md:w-1/2 flex flex-col overflow-hidden">
                <div className="mb-4">
                  <h3 className="text-sm font-medium mb-2">Exception Details</h3>
                  {currentException && (
                    <div className="space-y-2 text-sm">
                      <div className="grid grid-cols-2">
                        <span className="font-medium">Exception ID</span>
                        <span>{currentException.id}</span>
                      </div>
                      <div className="grid grid-cols-2">
                        <span className="font-medium">Lookup Type</span>
                        <span>{currentException.lookup_type}</span>
                      </div>
                      <div className="grid grid-cols-2">
                        <span className="font-medium">Lookup Field</span>
                        <span>{currentException.lookup_field}</span>
                      </div>
                      <div className="grid grid-cols-2">
                        <span className="font-medium">Lookup Value</span>
                        <span>{currentException.lookup_value}</span>
                      </div>
                      <div className="grid grid-cols-2">
                        <span className="font-medium">Error</span>
                        <span className="text-red-500">{currentException.exception_message}</span>
                      </div>
                    </div>
                  )}
                </div>
                
                {/* Potential matches */}
                {currentException && currentException.potential_matches && currentException.potential_matches.length > 0 && (
                  <div className="mb-4">
                    <h3 className="text-sm font-medium mb-2">Potential Matches</h3>
                    <div className="space-y-2">
                      {currentException.potential_matches.map((match, idx) => (
                        <div 
                          key={idx} 
                          className="flex items-center justify-between p-2 border rounded-md cursor-pointer hover:bg-muted/50"
                          onClick={() => {
                            setResolutionAction('accept');
                            setLookupValue(String(match.display));
                          }}
                        >
                          <span>{match.display}</span>
                          {match.score && (
                            <Badge variant="outline">{Math.round(match.score * 100)}%</Badge>
                          )}
                        </div>
                      ))}
                    </div>
                  </div>
                )}
                
                {/* Resolution form */}
                <div className="flex-1 overflow-y-auto">
                  <h3 className="text-sm font-medium mb-2">Resolve Exception</h3>
                  
                  <RadioGroup 
                    value={resolutionAction} 
                    onValueChange={(value) => setResolutionAction(value as any)}
                    className="mb-4"
                  >
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="accept" id="accept" />
                      <Label htmlFor="accept" className="cursor-pointer">Accept with value</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="reject" id="reject" />
                      <Label htmlFor="reject" className="cursor-pointer">Reject</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <RadioGroupItem value="for_creation" id="for_creation" />
                      <Label htmlFor="for_creation" className="cursor-pointer">Mark for entity creation</Label>
                    </div>
                  </RadioGroup>
                  
                  {resolutionAction === 'accept' && (
                    <div className="mb-4">
                      <Label htmlFor="lookup-value">Lookup Value</Label>
                      <Input 
                        id="lookup-value"
                        value={lookupValue}
                        onChange={(e) => setLookupValue(e.target.value)}
                        placeholder="Enter lookup value"
                        className="mt-1"
                        autoFocus
                      />
                    </div>
                  )}
                  
                  {/* Batch options */}
                  <div className="space-y-2 border-t pt-3 mt-4">
                    <div className="flex items-center space-x-2">
                      <Checkbox 
                        id="apply-to-similar" 
                        checked={applyToSimilar}
                        onCheckedChange={(checked) => setApplyToSimilar(!!checked)}
                      />
                      <Label htmlFor="apply-to-similar" className="cursor-pointer">
                        Apply to similar exceptions
                      </Label>
                    </div>
                    
                    {applyToSimilar && (
                      <div className="pl-6 space-y-2 text-sm">
                        <div className="flex items-center space-x-2">
                          <Checkbox 
                            id="similarity-type" 
                            checked={similarityOptions.lookup_type}
                            onCheckedChange={(checked) => 
                              setSimilarityOptions({
                                ...similarityOptions,
                                lookup_type: !!checked
                              })
                            }
                          />
                          <Label htmlFor="similarity-type" className="cursor-pointer">
                            Same lookup type
                          </Label>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <Checkbox 
                            id="similarity-field" 
                            checked={similarityOptions.lookup_field}
                            onCheckedChange={(checked) => 
                              setSimilarityOptions({
                                ...similarityOptions,
                                lookup_field: !!checked
                              })
                            }
                          />
                          <Label htmlFor="similarity-field" className="cursor-pointer">
                            Same lookup field
                          </Label>
                        </div>
                        
                        <div className="flex items-center space-x-2">
                          <Checkbox 
                            id="similarity-message" 
                            checked={similarityOptions.exception_message}
                            onCheckedChange={(checked) => 
                              setSimilarityOptions({
                                ...similarityOptions,
                                exception_message: !!checked
                              })
                            }
                          />
                          <Label htmlFor="similarity-message" className="cursor-pointer">
                            Same exception message
                          </Label>
                        </div>
                      </div>
                    )}
                  </div>
                  
                  <KeyboardShortcutHelp />
                </div>
              </div>
            </div>
            
            {/* Error message */}
            {error && (
              <div className="text-sm text-red-500 mt-2 mb-2">
                {error}
              </div>
            )}
            
            {/* Footer with navigation */}
            <DialogFooter className="flex items-center justify-between space-x-2">
              <div className="flex items-center space-x-2">
                <Button
                  variant="outline"
                  size="icon"
                  onClick={handlePrevious}
                  disabled={currentIndex <= 0}
                >
                  <ArrowLeft className="h-4 w-4" />
                </Button>
                <span className="text-sm text-muted-foreground">
                  {currentIndex + 1} of {exceptions.length}
                </span>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={handleNext}
                  disabled={currentIndex >= exceptions.length - 1}
                >
                  <ArrowRight className="h-4 w-4" />
                </Button>
              </div>
              
              <div className="flex items-center space-x-2">
                <Button variant="outline" onClick={onClose}>
                  Cancel
                </Button>
                <Button 
                  onClick={handleResolve} 
                  disabled={
                    isResolving || 
                    (resolutionAction === 'accept' && !lookupValue.trim())
                  }
                >
                  {isResolving ? (
                    <>
                      <Spinner className="mr-2 h-4 w-4" />
                      Resolving...
                    </>
                  ) : (
                    <>
                      {resolutionAction === 'accept' && <CheckCircle className="mr-2 h-4 w-4" />}
                      {resolutionAction === 'reject' && <XCircle className="mr-2 h-4 w-4" />}
                      {resolutionAction === 'for_creation' && <Plus className="mr-2 h-4 w-4" />}
                      {resolutionAction === 'accept' ? 'Accept' : 
                       resolutionAction === 'reject' ? 'Reject' : 'Mark for Creation'}
                    </>
                  )}
                </Button>
              </div>
            </DialogFooter>
          </>
        )}
      </DialogContent>
    </Dialog>
  );
};

export default LookupExceptionResolver;

```

## C:\xampp\htdocs\DocTypeGen\public\src\components\upload\FileUpload.tsx
```tsx
// src/components/upload/FileUpload.tsx
import React, { useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { FileUp, AlertCircle, Check, Loader2 } from 'lucide-react';
import { commandService } from "@/api/services";
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import config from "@/config";
import { formatFileSize } from '@/lib/utils';

// Convert accepted file types string to dropzone format
const parseAcceptedTypes = (types: string): Record<string, string[]> => {
  const result: Record<string, string[]> = {};
  
  types.split(',').forEach(type => {
    const trimmedType = type.trim();
    if (trimmedType.startsWith('.')) {
      // Handle extensions like .csv
      const ext = trimmedType.substring(1);
      switch (ext) {
        case 'csv':
          result['text/csv'] = [`.${ext}`];
          break;
        case 'xls':
          result['application/vnd.ms-excel'] = [`.${ext}`];
          break;
        case 'xlsx':
          result['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'] = [`.${ext}`];
          break;
        default:
          // Generic handling
          result[`application/${ext}`] = [`.${ext}`];
      }
    } else {
      // Handle MIME types directly
      result[trimmedType] = [];
    }
  });
  
  return result;
};

const FileUpload: React.FC = () => {
  const navigate = useNavigate();
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  // Get config values
  const MAX_FILE_SIZE = config.upload.maxFileSize;
  const ACCEPTED_FILE_TYPES = config.upload.acceptedFileTypes;
  
  // Handle file drop with react-dropzone
  const onDrop = useCallback((acceptedFiles: File[]) => {
    setError(null);
    
    // Validate file size
    const selectedFile = acceptedFiles[0];
    if (selectedFile.size > MAX_FILE_SIZE) {
      setError(`File size too large. Maximum allowed size is ${formatFileSize(MAX_FILE_SIZE)}.`);
      return;
    }
    
    // Handle file selection
    setFile(selectedFile);
  }, [MAX_FILE_SIZE]);
  
  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: parseAcceptedTypes(ACCEPTED_FILE_TYPES),
    multiple: false,
    maxSize: MAX_FILE_SIZE,
  });
  
  // Handle file upload
  const handleUpload = async () => {
    if (!file) return;
    
    setError(null);
    setUploading(true);
    setUploadProgress(0);
    
    try {
      // Simulate upload progress
      const progressInterval = setInterval(() => {
        setUploadProgress((prev) => {
          const newProgress = prev + Math.random() * 10;
          return newProgress >= 90 ? 90 : newProgress;
        });
      }, 300);
      
      // Upload the file
      const response = await commandService.uploadFile(file);
      
      // Clear interval and set progress to 100%
      clearInterval(progressInterval);
      setUploadProgress(100);
      
      if (response.success) {
        setSuccess(true);
        
        // Redirect to workflow page after a short delay
        setTimeout(() => {
          navigate(`/workflow?session=${response.result.hash}`);
        }, 1000);
      } else {
        setError(response.error || 'File upload failed. Please try again.');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'An error occurred during upload. Please try again.');
    } finally {
      setUploading(false);
    }
  };
  
  // Reset the component
  const handleReset = () => {
    setFile(null);
    setError(null);
    setSuccess(false);
    setUploadProgress(0);
  };

  return (
    <Card className="w-full max-w-3xl mx-auto">
      <CardHeader>
        <CardTitle>Import Data File</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        {success && (
          <Alert variant="success">
            <Check className="h-4 w-4" />
            <AlertTitle>Success</AlertTitle>
            <AlertDescription>
              File uploaded successfully! Redirecting to workflow...
            </AlertDescription>
          </Alert>
        )}
        
        <div
          {...getRootProps()}
          className={`
            border-2 border-dashed rounded-lg p-8 text-center
            transition-colors cursor-pointer
            ${isDragActive ? 'border-primary bg-primary/5' : 'border-muted-foreground/25'}
            ${file ? 'bg-muted/50' : ''}
          `}
        >
          <input {...getInputProps()} />
          <div className="flex flex-col items-center justify-center space-y-2">
            <FileUp className="h-8 w-8 text-muted-foreground" />
            {file ? (
              <>
                <p className="text-sm font-medium">{file.name}</p>
                <p className="text-xs text-muted-foreground">
                  {formatFileSize(file.size)}
                </p>
              </>
            ) : (
              <>
                <p className="text-sm font-medium">
                  {isDragActive ? 'Drop the file here' : 'Drag and drop your file here'}
                </p>
                <p className="text-xs text-muted-foreground">
                  Supported formats: {ACCEPTED_FILE_TYPES} (max {formatFileSize(MAX_FILE_SIZE)})
                </p>
              </>
            )}
          </div>
        </div>
        
        {uploading && (
          <div className="space-y-2">
            <div className="flex justify-between text-xs">
              <span>Uploading...</span>
              <span>{Math.round(uploadProgress)}%</span>
            </div>
            <Progress value={uploadProgress} />
          </div>
        )}
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button
          variant="outline"
          onClick={handleReset}
          disabled={uploading || !file}
        >
          Reset
        </Button>
        <Button
          onClick={handleUpload}
          disabled={uploading || !file || success}
        >
          {uploading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Uploading...
            </>
          ) : (
            'Upload & Process'
          )}
        </Button>
      </CardFooter>
    </Card>
  );
};

export default FileUpload;
```

## C:\xampp\htdocs\DocTypeGen\public\src\components\workflow\EntityCreationStep.tsx
```tsx
// src/components/workflow/EntityCreationStep.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { commandService } from '@/api/services';
import { CommandResponse, EntitiesForCreationResult, Entity, EntityCreationResult } from '@/types';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Spinner } from '@/components/ui/spinner';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { AlertCircle, CheckCircle, FileText, Database } from 'lucide-react';
import { toast } from '@/components/ui/use-toast';

interface EntityCreationStepProps {
  onComplete: (result: CommandResponse) => void;
}

const EntityCreationStep: React.FC<EntityCreationStepProps> = ({ onComplete }) => {
  const navigate = useNavigate();
  
  const [isLoading, setIsLoading] = useState(true);
  const [isCreating, setIsCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [entities, setEntities] = useState<EntitiesForCreationResult>({ entities: [], total: 0 });
  const [selectedEntityIndex, setSelectedEntityIndex] = useState<number | null>(null);
  const [entityForm, setEntityForm] = useState<Entity>({
    entity_type: '',
    name: '',
    properties: {}
  });
  
  useEffect(() => {
    loadEntitiesForCreation();
  }, []);
  
  const loadEntitiesForCreation = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await commandService.getEntitiesForCreation();
      setEntities(result);
      
      if (result.entities.length > 0) {
        // Pre-select the first entity
        selectEntity(0);
      }
    } catch (err: any) {
      console.error('Error loading entities for creation:', err);
      setError(err.message || 'Failed to load entities for creation');
    } finally {
      setIsLoading(false);
    }
  };
  
  const selectEntity = (index: number) => {
    if (index >= 0 && index < entities.entities.length) {
      setSelectedEntityIndex(index);
      const entityData = entities.entities[index];
      
      // Initialize the form with entity data
      setEntityForm({
        entity_type: entityData.entity_type,
        name: entityData.lookup_value,
        properties: { ...entityData.sample_data }
      });
    }
  };
  
  const handleInputChange = (field: string, value: string) => {
    if (field === 'name') {
      setEntityForm({ ...entityForm, name: value });
    } else {
      setEntityForm({
        ...entityForm,
        properties: {
          ...entityForm.properties,
          [field]: value
        }
      });
    }
  };
  
  const handleCreateEntity = async () => {
    if (selectedEntityIndex === null) return;
    
    setIsCreating(true);
    setError(null);
    
    try {
      const result = await commandService.createEntity(entityForm);
      
      if (result.status === 'success') {
        toast({
          title: 'Entity Created',
          description: `Successfully created ${entityForm.entity_type} entity: ${entityForm.name}`,
          duration: 3000
        });
        
        // Remove the created entity from the list
        const updatedEntities = [...entities.entities];
        updatedEntities.splice(selectedEntityIndex, 1);
        
        setEntities({
          entities: updatedEntities,
          total: updatedEntities.length
        });
        
        // Select the next entity or reset if none left
        if (updatedEntities.length > 0) {
          selectEntity(selectedEntityIndex < updatedEntities.length ? selectedEntityIndex : 0);
        } else {
          setSelectedEntityIndex(null);
        }
      } else {
        setError(result.message);
      }
    } catch (err: any) {
      console.error('Error creating entity:', err);
      setError(err.message || 'Failed to create entity');
    } finally {
      setIsCreating(false);
    }
  };
  
  const handleCreateAll = async () => {
    // This would handle batch creation of all entities
    // For now, we'll just show a toast message
    toast({
      title: 'Batch Creation',
      description: 'Batch entity creation feature is coming soon',
      duration: 3000
    });
  };
  
  const goBack = () => {
    navigate('/workflow/lookups');
  };
  
  const goNext = () => {
    navigate('/workflow/sync');
    
    // Call onComplete with a success result
    onComplete({
      success: true,
      command: 'entity_creation',
      result: { status: 'success', message: 'Entity creation completed' }
    });
  };
  
  if (isLoading) {
    return (
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center justify-center py-8">
            <Spinner size="lg" />
            <span className="ml-2">Loading entities for creation...</span>
          </div>
        </CardContent>
      </Card>
    );
  }
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Entity Creation</CardTitle>
        <CardDescription>Create missing entities from lookup exceptions</CardDescription>
      </CardHeader>
      
      <CardContent>
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        {entities.entities.length === 0 ? (
          <div className="text-center py-12">
            <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No Entities to Create</h3>
            <p className="text-muted-foreground">
              There are no entities marked for creation. You can proceed to the next step.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Entity List */}
            <div className="md:col-span-1 border rounded-md overflow-hidden">
              <div className="bg-muted p-3 border-b">
                <h3 className="font-medium">Entities for Creation ({entities.total})</h3>
              </div>
              <div className="overflow-auto max-h-[400px]">
                <Table>
                  <TableBody>
                    {entities.entities.map((entity, index) => (
                      <TableRow 
                        key={index}
                        className={selectedEntityIndex === index ? 'bg-muted' : ''}
                        onClick={() => selectEntity(index)}
                      >
                        <TableCell>
                          <div className="font-medium">{entity.lookup_value}</div>
                          <div className="text-xs text-muted-foreground">{entity.entity_type}</div>
                        </TableCell>
                        <TableCell className="text-right">
                          <Badge>{entity.exception_count}</Badge>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
              
              <div className="p-3 border-t">
                <Button 
                  variant="outline" 
                  className="w-full" 
                  onClick={handleCreateAll}
                >
                  <Database className="mr-2 h-4 w-4" />
                  Create All
                </Button>
              </div>
            </div>
            
            {/* Entity Form */}
            <div className="md:col-span-2 border rounded-md overflow-hidden">
              {selectedEntityIndex !== null ? (
                <>
                  <div className="bg-muted p-3 border-b">
                    <h3 className="font-medium">
                      Create {entityForm.entity_type}: {entityForm.name}
                    </h3>
                  </div>
                  
                  <div className="p-4 space-y-4 overflow-auto max-h-[400px]">
                    <div>
                      <Label htmlFor="entity-name">Entity Name</Label>
                      <Input 
                        id="entity-name"
                        value={entityForm.name}
                        onChange={(e) => handleInputChange('name', e.target.value)}
                        className="mt-1"
                      />
                    </div>
                    
                    <div className="border-t pt-3">
                      <h4 className="text-sm font-medium mb-2">Properties</h4>
                      <div className="space-y-3">
                        {Object.entries(entityForm.properties).map(([key, value]) => (
                          <div key={key}>
                            <Label htmlFor={`property-${key}`}>{key}</Label>
                            <Input 
                              id={`property-${key}`}
                              value={value as string}
                              onChange={(e) => handleInputChange(key, e.target.value)}
                              className="mt-1"
                            />
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                  
                  <div className="p-3 border-t flex justify-end">
                    <Button 
                      onClick={handleCreateEntity}
                      disabled={isCreating || !entityForm.name.trim()}
                    >
                      {isCreating ? (
                        <>
                          <Spinner className="mr-2 h-4 w-4" />
                          Creating...
                        </>
                      ) : (
                        <>
                          <CheckCircle className="mr-2 h-4 w-4" />
                          Create Entity
                        </>
                      )}
                    </Button>
                  </div>
                </>
              ) : (
                <div className="flex items-center justify-center py-12 px-4 text-center">
                  <div>
                    <FileText className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
                    <h3 className="text-lg font-medium mb-2">No Entity Selected</h3>
                    <p className="text-muted-foreground">
                      Select an entity from the list to create it.
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </CardContent>
      
      <CardFooter className="flex justify-between">
        <Button variant="outline" onClick={goBack}>Back</Button>
        <Button onClick={goNext}>
          Next: Data Sync
        </Button>
      </CardFooter>
    </Card>
  );
};

export default EntityCreationStep;

```

## C:\xampp\htdocs\DocTypeGen\public\src\components\workflow\HtmlGenerationStep.tsx
```tsx
// src/components/workflow/HtmlGenerationStep.tsx
import React, { useState, useEffect } from 'react';
import { AlertCircle, Check, Loader2, ExternalLink } from 'lucide-react';
import { commandService } from "@/api/services";
import { CommandResponse, HtmlGenerationResult } from "@/types";
import { Button } from '../ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '../ui/card';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../ui/table';
import { Progress } from '../ui/progress';
import { Badge } from '../ui/badge';

interface HtmlGenerationStepProps {
  onComplete: (result: CommandResponse) => void;
}

const HtmlGenerationStep: React.FC<HtmlGenerationStepProps> = ({ onComplete }) => {
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationResult, setGenerationResult] = useState<HtmlGenerationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  
  // Start generation on mount
  useEffect(() => {
    generateHtml();
  }, []);
  
  const generateHtml = async () => {
    setIsGenerating(true);
    setError(null);
    setProgress(0);
    
    // Simulate progress
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        const newProgress = prev + Math.random() * 10;
        return newProgress >= 90 ? 90 : newProgress;
      });
    }, 300);
    
    try {
      const response = await commandService.runCommand('html');
      
      // Clear interval and set progress to 100%
      clearInterval(progressInterval);
      setProgress(100);
      
      if (response.success) {
        setGenerationResult(response.result);
      } else {
        setError(response.error || 'HTML generation failed. Please try again.');
      }
      
      setIsGenerating(false);
      return response;
    } catch (err: any) {
      clearInterval(progressInterval);
      setError(err.response?.data?.error || 'An error occurred during HTML generation. Please try again.');
      setIsGenerating(false);
      throw err;
    }
  };
  
  const handleContinue = async () => {
    if (!generationResult) return;
    
    try {
      const response = await commandService.runCommand('html');
      onComplete(response);
    } catch (err) {
      console.error('Error completing HTML generation step:', err);
      setError('Failed to continue to the next step. Please try again.');
    }
  };
  
  const handleRetry = () => {
    generateHtml();
  };
  
  const viewHtmlFile = (fileName: string) => {
    // Construct URL to HTML file
    // This depends on how your backend serves static files
    const baseUrl = window.location.origin;
    const sessionHash = generationResult?.output_dir.split('/').pop() || '';
    const url = `${baseUrl}/static/${sessionHash}/html/${fileName}`;
    window.open(url, '_blank');
  };

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle>HTML Generation</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        {isGenerating && (
          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span>Generating HTML files...</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <Progress value={progress} />
            </div>
            <div className="flex items-center justify-center py-8">
              <Loader2 className="mr-2 h-6 w-6 animate-spin text-primary" />
              <span>Generating HTML files from template...</span>
            </div>
          </div>
        )}
        
        {!isGenerating && generationResult && (
          <div className="space-y-6">
            <Alert variant={generationResult.errors.length === 0 ? "success" : "warning"}>
              <Check className="h-4 w-4" />
              <AlertTitle>HTML Generation Complete</AlertTitle>
              <AlertDescription>
                Generated {generationResult.num_files} HTML files using template "{generationResult.template_name}"
                {generationResult.errors.length > 0 && (
                  <>. <span className="font-semibold text-warning">Warning: {generationResult.errors.length} files had errors</span></>
                )}
              </AlertDescription>
            </Alert>
            
            <div>
              <h3 className="font-medium mb-2">Generation Summary</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="border rounded-md p-4">
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Files Generated:</span>
                      <span className="font-medium">{generationResult.num_files}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Template:</span>
                      <span className="font-medium">{generationResult.template_name}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Output Directory:</span>
                      <span className="font-medium truncate max-w-[200px]" title={generationResult.output_dir}>
                        {generationResult.output_dir}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Errors:</span>
                      <span className="font-medium">{generationResult.errors.length}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div>
              <h3 className="font-medium mb-2">Generated HTML Files</h3>
              <div className="rounded-md border overflow-hidden">
                <div className="max-h-64 overflow-y-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-12">#</TableHead>
                        <TableHead>File Name</TableHead>
                        <TableHead className="text-right">Action</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {generationResult.html_files.slice(0, 10).map((fileName, index) => (
                        <TableRow key={index}>
                          <TableCell>{index + 1}</TableCell>
                          <TableCell className="font-mono text-xs">{fileName}</TableCell>
                          <TableCell className="text-right">
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => viewHtmlFile(fileName)}
                            >
                              <ExternalLink className="h-4 w-4 mr-1" />
                              View
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                      {generationResult.html_files.length > 10 && (
                        <TableRow>
                          <TableCell colSpan={3} className="text-center text-muted-foreground">
                            +{generationResult.html_files.length - 10} more files
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </div>
              </div>
            </div>
            
            {generationResult.errors.length > 0 && (
              <div>
                <h3 className="font-medium mb-2">Generation Errors</h3>
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Row</TableHead>
                        <TableHead>Error</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {generationResult.errors.map((error, index) => (
                        <TableRow key={index}>
                          <TableCell>Row {error.row}</TableCell>
                          <TableCell>{error.error}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button
          variant="outline"
          onClick={handleRetry}
          disabled={isGenerating}
        >
          Regenerate HTML
        </Button>
        <Button
          onClick={handleContinue}
          disabled={isGenerating || !generationResult}
        >
          Continue to PDF Generation
        </Button>
      </CardFooter>
    </Card>
  );
};

export default HtmlGenerationStep;
```

## C:\xampp\htdocs\DocTypeGen\public\src\components\workflow\LookupResolutionStep.tsx
```tsx
// src/components/workflow/LookupResolutionStep.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { commandService } from '@/api/services';
import { LookupResolutionResult, CommandResponse, LookupException } from '@/types';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Spinner } from '@/components/ui/spinner';
import { AlertCircle, CheckCircle, AlertTriangle, FileText, Play, Plus, RotateCw, Wrench } from 'lucide-react';
import DocumentsTable from '@/components/lookup/DocumentsTable';
import ExceptionsTable from '@/components/lookup/ExceptionsTable';
import ForCreationTable from '@/components/lookup/ForCreationTable';
import LookupExceptionResolver from '@/components/lookup/LookupExceptionResolver';

interface StatusCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  color?: string;
}

const StatusCard: React.FC<StatusCardProps> = ({ title, value, icon, color = 'default' }) => {
  const colorClasses = {
    'default': 'bg-card',
    'green': 'bg-green-50 border-green-200 text-green-800',
    'amber': 'bg-amber-50 border-amber-200 text-amber-800',
    'blue': 'bg-blue-50 border-blue-200 text-blue-800',
    'red': 'bg-red-50 border-red-200 text-red-800',
  };

  return (
    <div className={`flex items-center p-4 border rounded-lg ${colorClasses[color as keyof typeof colorClasses]}`}>
      <div className="mr-4">{icon}</div>
      <div>
        <div className="text-sm font-medium">{title}</div>
        <div className="text-2xl font-bold">{value}</div>
      </div>
    </div>
  );
};

interface LookupResolutionStepProps {
  onComplete: (result: CommandResponse) => void;
}

const LookupResolutionStep: React.FC<LookupResolutionStepProps> = ({ onComplete }) => {
  const navigate = useNavigate();
  
  const [isResolving, setIsResolving] = useState(false);
  const [isExceptionResolverOpen, setIsExceptionResolverOpen] = useState(false);
  const [selectedExceptionId, setSelectedExceptionId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<LookupResolutionResult | null>(null);
  
  const [stats, setStats] = useState({
    total: 0,
    resolved: 0,
    exceptions: 0,
    forCreation: 0
  });
  
  // Properly type the state variables with the imported LookupException interface
  const [allDocuments, setAllDocuments] = useState<LookupException[]>([]);
  const [resolvedDocuments, setResolvedDocuments] = useState<LookupException[]>([]);
  const [exceptions, setExceptions] = useState<LookupException[]>([]);
  const [forCreationDocuments, setForCreationDocuments] = useState<LookupException[]>([]);
  
  useEffect(() => {
    // Fetch initial status
    fetchLookupStatus();
  }, []);
  
  const fetchLookupStatus = async () => {
    try {
      const exceptionsData = await commandService.getLookupExceptions();
      setExceptions(exceptionsData.exceptions);
      
      setStats({
        total: exceptionsData.total,
        resolved: exceptionsData.resolved,
        exceptions: exceptionsData.pending,
        forCreation: exceptionsData.for_creation
      });
      
      // For now, we'll use the exceptions data to populate our tables
      // In a real implementation, we'd have separate endpoints for each document category
      setAllDocuments(exceptionsData.exceptions);
      
      const resolvedDocs = exceptionsData.exceptions.filter(
        (exc: LookupException) => exc.status === 'accepted' || exc.status === 'rejected'
      );
      setResolvedDocuments(resolvedDocs);
      
      const forCreationDocs = exceptionsData.exceptions.filter(
        (exc: LookupException) => exc.status === 'for_creation'
      );
      setForCreationDocuments(forCreationDocs);
      
    } catch (err) {
      console.error('Error fetching lookup status:', err);
      setError('Failed to load lookup status. Please try again.');
    }
  };
  
  const handleResolve = async () => {
    setIsResolving(true);
    setError(null);
    
    try {
      const result = await commandService.resolveLookups();
      setResult(result);
      
      if (result.status === 'success') {
        // Update our stats based on the result
        setStats({
          total: result.records_processed,
          resolved: result.successful_lookups,
          exceptions: result.exceptions,
          forCreation: result.for_creation
        });
        
        // Refresh the data
        await fetchLookupStatus();
      } else {
        setError(result.message);
      }
    } catch (err: any) {
      console.error('Error resolving lookups:', err);
      setError(err.message || 'Failed to resolve lookups. Please try again.');
    } finally {
      setIsResolving(false);
    }
  };
  
  const openExceptionResolver = () => {
    setSelectedExceptionId(null);
    setIsExceptionResolverOpen(true);
  };
  
  const openExceptionResolverWithId = (id: number) => {
    setSelectedExceptionId(id);
    setIsExceptionResolverOpen(true);
  };
  
  const handleExceptionResolved = async () => {
    // Refresh data after an exception is resolved
    await fetchLookupStatus();
  };
  
  const goBack = () => {
    navigate('/workflow/pdf');
  };
  
  const goNext = () => {
    // Only go to entity creation if there are entities to create
    if (stats.forCreation > 0) {
      navigate('/workflow/entity-creation');
    } else {
      navigate('/workflow/sync');
    }
    
    // Call onComplete with a success result
    onComplete({
      success: true,
      command: 'resolve_lookups',
      result: { status: 'success', message: 'Lookup resolution completed' }
    });
  };
  
  const canProceed = stats.exceptions === 0; // Can only proceed if all exceptions are resolved
  
  return (
    <>
      <Card>
        <CardHeader>
          <CardTitle>Lookup Resolution</CardTitle>
          <CardDescription>Match documents to external data sources</CardDescription>
        </CardHeader>
        
        <CardContent>
          {error && (
            <Alert variant="destructive" className="mb-6">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          
          {/* Status Overview */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <StatusCard title="Total Documents" value={stats.total} icon={<FileText className="h-5 w-5" />} />
            <StatusCard 
              title="Resolved" 
              value={stats.resolved} 
              icon={<CheckCircle className="h-5 w-5 text-green-600" />} 
              color="green" 
            />
            <StatusCard 
              title="Exceptions" 
              value={stats.exceptions} 
              icon={<AlertTriangle className="h-5 w-5 text-amber-600" />} 
              color="amber" 
            />
            <StatusCard 
              title="For Creation" 
              value={stats.forCreation} 
              icon={<Plus className="h-5 w-5 text-blue-600" />} 
              color="blue" 
            />
          </div>
          
          {/* Actions Panel */}
          <div className="flex flex-wrap gap-4 mb-6">
            <Button 
              onClick={handleResolve} 
              disabled={isResolving || stats.total === 0}
            >
              {isResolving ? (
                <>
                  <Spinner className="mr-2 h-4 w-4" />
                  Resolving...
                </>
              ) : (
                <>
                  <Play className="mr-2 h-4 w-4" />
                  Resolve Lookups
                </>
              )}
            </Button>
            
            <Button 
              variant="outline" 
              onClick={fetchLookupStatus}
              disabled={isResolving}
            >
              <RotateCw className="mr-2 h-4 w-4" />
              Refresh Status
            </Button>
            
            {stats.exceptions > 0 && (
              <Button variant="outline" onClick={openExceptionResolver}>
                <Wrench className="mr-2 h-4 w-4" />
                Resolve Exceptions
              </Button>
            )}
          </div>
          
          {/* Results Tabs */}
          <Tabs defaultValue="all">
            <TabsList>
              <TabsTrigger value="all">All Documents ({stats.total})</TabsTrigger>
              <TabsTrigger value="resolved">Resolved ({stats.resolved})</TabsTrigger>
              <TabsTrigger value="exceptions">Exceptions ({stats.exceptions})</TabsTrigger>
              <TabsTrigger value="creation">For Creation ({stats.forCreation})</TabsTrigger>
            </TabsList>
            
            <TabsContent value="all">
              <DocumentsTable documents={allDocuments} />
            </TabsContent>
            
            <TabsContent value="resolved">
              <DocumentsTable documents={resolvedDocuments} />
            </TabsContent>
            
            <TabsContent value="exceptions">
              <ExceptionsTable 
                exceptions={exceptions} 
                onResolve={openExceptionResolverWithId} 
              />
            </TabsContent>
            
            <TabsContent value="creation">
              <ForCreationTable documents={forCreationDocuments} />
            </TabsContent>
          </Tabs>
        </CardContent>
        
        <CardFooter className="flex justify-between">
          <Button variant="outline" onClick={goBack}>Back</Button>
          <Button onClick={goNext} disabled={!canProceed}>
            {stats.forCreation > 0 ? 'Next: Entity Creation' : 'Next: Data Sync'}
          </Button>
        </CardFooter>
      </Card>
      
      {/* Exception Resolver Dialog */}
      <LookupExceptionResolver 
        isOpen={isExceptionResolverOpen}
        onClose={() => setIsExceptionResolverOpen(false)}
        exceptionId={selectedExceptionId}
        onResolved={handleExceptionResolved}
      />
    </>
  );
};

export default LookupResolutionStep;

```

## C:\xampp\htdocs\DocTypeGen\public\src\components\workflow\MappingStep.tsx
```tsx
// src/components/workflow/MappingStep.tsx
import React, { useState, useEffect, useRef } from 'react';
import { AlertCircle, Check, Loader2, Edit, Save } from 'lucide-react';
import { commandService } from "@/api/services";
import { CommandResponse, ValidationResult, MappingResult } from "@/types";
import { Button } from '../ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '../ui/card';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../ui/table';
import { Badge } from '../ui/badge';
import { Label } from '../ui/label';
import { Progress } from '../ui/progress';
import { ScrollArea } from '../ui/scroll-area';

interface MappingStepProps {
  onComplete: (result: CommandResponse) => void;
  validationResult?: ValidationResult;
}

const MappingStep: React.FC<MappingStepProps> = ({ onComplete, validationResult }) => {
  const [isMapping, setIsMapping] = useState(false);
  const [mappingResult, setMappingResult] = useState<MappingResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  const [tableColumns, setTableColumns] = useState<string[]>([]);
  
  // For editing mappings
  const [editMode, setEditMode] = useState(false);
  const [editedMappings, setEditedMappings] = useState<Record<string, any>>({});
  const [currentColumn, setCurrentColumn] = useState<{name: string, type: string | null}>({name: '', type: null});
  
  const editButtonRef = useRef<HTMLButtonElement>(null);
  
  // Start mapping on mount
  useEffect(() => {
    generateMapping();
    
    // Get table columns from validation results or API
    if (validationResult) {
      extractTableColumns();
    }
  }, [validationResult]);
  
  const extractTableColumns = async () => {
    try {
      // First try to extract columns from validation result if available
      if (validationResult?.field_matches) {
        const columns = new Set<string>();
        
        // Add all matched columns
        Object.values(validationResult.field_matches).forEach(match => {
          if (match.column) columns.add(match.column);
        });
        
        if (columns.size > 0) {
          setTableColumns(Array.from(columns));
          return;
        }
      }
      
      // Fallback: try to get table data from existing API
      try {
        // This uses the existing table_data API endpoint
        const response = await commandService.runCommand('table_data');
        
        if (response.success && response.result?.columns) {
          setTableColumns(response.result.columns);
        } else {
          console.error('Failed to fetch table data:', response.error);
        }
      } catch (err) {
        console.error('Error fetching table data:', err);
      }
    } catch (err) {
      console.error('Error extracting table columns:', err);
    }
  };
  
  const generateMapping = async () => {
    setIsMapping(true);
    setError(null);
    setProgress(0);
    
    // Simulate progress
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        const newProgress = prev + Math.random() * 10;
        return newProgress >= 90 ? 90 : newProgress;
      });
    }, 300);
    
    try {
      const response = await commandService.runCommand('map');
      
      // Clear interval and set progress to 100%
      clearInterval(progressInterval);
      setProgress(100);
      
      if (response.success) {
        setMappingResult(response.result);
        
        // Set the edited mappings from the result
        if (response.result.mapped_fields) {
          setEditedMappings(response.result.mapped_fields);
        }
      } else {
        setError(response.error || 'Mapping generation failed. Please try again.');
      }
      
      setIsMapping(false);
      return response;
    } catch (err: any) {
      clearInterval(progressInterval);
      setError(err.response?.data?.error || 'An error occurred during mapping. Please try again.');
      setIsMapping(false);
      throw err;
    }
  };
  
  const handleContinue = async () => {
    if (!mappingResult) return;
    
    try {
      // If mappings were edited, update them first
      let response;
      
      if (editMode) {
        response = await commandService.updateMapping(editedMappings);
      } else {
        response = await commandService.runCommand('map');
      }
      
      onComplete(response as CommandResponse);
    } catch (err) {
      console.error('Error completing mapping step:', err);
      setError('Failed to continue to the next step. Please try again.');
    }
  };
  
  const handleRetry = () => {
    generateMapping();
  };
  
  const handleValidateWithMappings = async () => {
    setIsMapping(true);
    setError(null);
    
    try {
      // First save the mappings
      await handleSaveMapping();
      
      // Then run validation using the updated mappings
      const response = await commandService.runCommand('validate');
      
      if (response.success) {
        // Update with the new validation results
        setMappingResult(response.result);
      } else {
        setError(response.error || 'Validation failed. Please check your mappings.');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'An error occurred during validation. Please try again.');
    } finally {
      setIsMapping(false);
    }
  };
  
  const handleEditMapping = () => {
    setEditMode(true);
  };
  
  const handleSaveMapping = async () => {
    setIsMapping(true);
    setError(null);
    
    try {
      const response = await commandService.updateMapping(editedMappings);
      
      if (response) {
        setMappingResult(response);
        setEditMode(false);
      } else {
        setError('Failed to update mappings. Please try again.');
      }
    } catch (err: any) {
      setError(err.response?.data?.error || 'An error occurred while updating mappings. Please try again.');
    } finally {
      setIsMapping(false);
    }
  };
  
  const handleSelectType = (column: string, typeName: string) => {
    if (!typeName) {
      // If unselecting, remove the mapping
      const newMappings = { ...editedMappings };
      delete newMappings[column];
      setEditedMappings(newMappings);
      return;
    }
    
    // Get the full type info from schema
    const typeInfo = mappingResult?.schema_fields[typeName];
    if (!typeInfo) {
      console.error(`Type ${typeName} not found in schema`);
      return;
    }
    
    // Create a complete mapping object by copying ALL properties from the type definition
    // This ensures we match the format in docs/validation/mapping,example.json
    const completeMapping: Record<string, any> = {
      type: typeName,
      validation_type: typeInfo.validate_type,
      required: typeInfo.required || false,
      description: typeInfo.description,
      slug: typeInfo.slug || [typeName]
    };
    
    // Copy all other properties from the type definition
    Object.entries(typeInfo).forEach(([key, value]) => {
      // Skip properties we've already set above
      if (!['validate_type', 'required', 'description', 'slug'].includes(key)) {
        completeMapping[key] = value;
      }
    });
    
    // Update the mappings
    setEditedMappings({
      ...editedMappings,
      [column]: completeMapping
    });
  };
  
  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle>Field Mapping</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        {isMapping && (
          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span>Generating field mapping...</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <Progress value={progress} />
            </div>
            <div className="flex items-center justify-center py-8">
              <Loader2 className="mr-2 h-6 w-6 animate-spin text-primary" />
              <span>Generating field-to-column mapping...</span>
            </div>
          </div>
        )}
        
        {!isMapping && mappingResult && (
          <div className="space-y-6">
            <Alert variant={(mappingResult.missing_required?.length ?? 0) === 0 ? "success" : "warning"}>
              <Check className="h-4 w-4" />
              <AlertTitle>Mapping Generated</AlertTitle>
              <AlertDescription>
                {Object.keys(mappingResult.mapped_fields).length} fields mapped successfully
                {mappingResult.missing_required && mappingResult.missing_required.length > 0 && (
                  <>. <span className="font-semibold text-warning">Warning: {mappingResult.missing_required.length} required fields not mapped</span></>
                )}
              </AlertDescription>
            </Alert>
            
            <div className="flex items-center justify-between">
              <h3 className="font-medium">Column to Type Mapping</h3>
              {!editMode ? (
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={handleEditMapping}
                  ref={editButtonRef}
                >
                  <Edit className="mr-2 h-4 w-4" />
                  Edit Mapping
                </Button>
              ) : (
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={handleSaveMapping}
                  disabled={isMapping}
                >
                  <Save className="mr-2 h-4 w-4" />
                  Save Changes
                </Button>
              )}
            </div>
            
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Column Name</TableHead>
                    <TableHead>Matched Type</TableHead>
                    <TableHead>Validation Type</TableHead>
                    {editMode && <TableHead className="text-right">Action</TableHead>}
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {tableColumns.map((column) => {
                    const mapping = editedMappings[column] || null;
                    const mappedType = mapping?.type || null;
                    const typeInfo = mappedType ? mappingResult.schema_fields[mappedType] : null;
                    const isRequired = typeInfo?.required === true;
                    
                    return (
                      <TableRow key={column} className={isRequired && !mappedType ? "bg-warning/10" : undefined}>
                        <TableCell className="font-medium">{column}</TableCell>
                        <TableCell>
                          {mappedType ? (
                            <span>{mappedType}</span>
                          ) : (
                            <span className="text-muted-foreground italic">Unknown</span>
                          )}
                        </TableCell>
                        <TableCell>
                          {mapping?.validation_type ? (
                            <Badge 
                              variant={isRequired ? "default" : "outline"}
                            >
                              {mapping.validation_type}
                            </Badge>
                          ) : (
                            <span className="text-muted-foreground">string</span>
                          )}
                        </TableCell>
                        {editMode && (
                          <TableCell className="text-right">
                            <div className="border rounded p-1 w-full h-64 overflow-auto bg-white">
                              <div 
                                className="p-2 hover:bg-gray-100 cursor-pointer border-b"
                                onClick={() => handleSelectType(column, "")}
                              >
                                <span className="text-gray-500">None (unmapped)</span>
                              </div>
                              {mappingResult && Object.keys(mappingResult.schema_fields).map((typeName) => {
                                const typeInfo = mappingResult.schema_fields[typeName];
                                return (
                                  <div 
                                    key={typeName} 
                                    className={`p-2 cursor-pointer border-b hover:bg-gray-100 ${mappedType === typeName ? 'bg-blue-50' : ''}`}
                                    onClick={() => handleSelectType(column, typeName)}
                                  >
                                    <div className="font-bold">{typeName}</div>
                                    <div>
                                      <span className="font-semibold mr-1">Type:</span>{typeInfo.validate_type}
                                      {typeInfo.required && <span className="ml-2 text-red-500 font-bold">Required</span>}
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          </TableCell>
                        )}
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          </div>
        )}
      </CardContent>
      <CardFooter className="flex justify-between">
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={handleRetry}
            disabled={isMapping}
          >
            Regenerate Mapping
          </Button>
          {editMode && (
            <Button 
              variant="secondary"
              onClick={handleValidateWithMappings}
              disabled={isMapping}
            >
              Validate with Mappings
            </Button>
          )}
        </div>
        <Button
          onClick={handleContinue}
          disabled={isMapping || !mappingResult}
        >
          Continue to HTML Generation
        </Button>
      </CardFooter>
    </Card>
  );
};

export default MappingStep;
```

## C:\xampp\htdocs\DocTypeGen\public\src\components\workflow\PdfGenerationStep.tsx
```tsx
// src/components/workflow/PdfGenerationStep.tsx
import React, { useState, useEffect } from 'react';
import { AlertCircle, Check, Loader2, ExternalLink, Download } from 'lucide-react';
import { commandService } from "@/api/services";
import { CommandResponse, PdfGenerationResult } from "@/types";
import { Button } from '../ui/button';
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '../ui/card';
import { Alert, AlertDescription, AlertTitle } from '../ui/alert';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../ui/table';
import { Progress } from '../ui/progress';
import { useNavigate } from 'react-router-dom';

interface PdfGenerationStepProps {
  onComplete: (result: CommandResponse) => void;
}

const PdfGenerationStep: React.FC<PdfGenerationStepProps> = ({ onComplete }) => {
  const navigate = useNavigate();
  const [isGenerating, setIsGenerating] = useState(false);
  const [generationResult, setGenerationResult] = useState<PdfGenerationResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [progress, setProgress] = useState(0);
  
  // Start generation on mount
  useEffect(() => {
    generatePdf();
  }, []);
  
  const generatePdf = async () => {
    setIsGenerating(true);
    setError(null);
    setProgress(0);
    
    // Simulate progress
    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        const newProgress = prev + Math.random() * 5;
        return newProgress >= 90 ? 90 : newProgress;
      });
    }, 500);
    
    try {
      const response = await commandService.runCommand('pdf');
      
      // Clear interval and set progress to 100%
      clearInterval(progressInterval);
      setProgress(100);
      
      if (response.success) {
        setGenerationResult(response.result);
      } else {
        setError(response.error || 'PDF generation failed. Please try again.');
      }
      
      setIsGenerating(false);
      return response;
    } catch (err: any) {
      clearInterval(progressInterval);
      setError(err.response?.data?.error || 'An error occurred during PDF generation. Please try again.');
      setIsGenerating(false);
      throw err;
    }
  };
  
  const handleComplete = async () => {
    if (!generationResult) return;
    
    try {
      const response = await commandService.runCommand('pdf');
      onComplete(response);
      
      // Get session hash and navigate to logs
      const status = await commandService.getStatus();
      if (status.session_hash) {
        navigate(`/logs/${status.session_hash}`);
      } else {
        navigate('/logs');
      }
    } catch (err) {
      console.error('Error completing PDF generation step:', err);
      setError('Failed to complete the process. Please try again.');
    }
  };
  
  const handleRetry = () => {
    generatePdf();
  };
  
  const viewPdfFile = (fileName: string) => {
    // Construct URL to PDF file
    const baseUrl = window.location.origin;
    const sessionHash = generationResult?.log_file.split('/').pop()?.split('_')[0] || '';
    const url = `${baseUrl}/static/${sessionHash}/pdf/${fileName}`;
    window.open(url, '_blank');
  };
  
  const downloadPdfFile = (fileName: string) => {
    // Construct URL and trigger download
    const baseUrl = window.location.origin;
    const sessionHash = generationResult?.log_file.split('/').pop()?.split('_')[0] || '';
    const url = `${baseUrl}/static/${sessionHash}/pdf/${fileName}`;
    
    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };

  return (
    <Card className="w-full max-w-4xl mx-auto">
      <CardHeader>
        <CardTitle>PDF Generation</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {error && (
          <Alert variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        {isGenerating && (
          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between text-xs">
                <span>Generating PDF files...</span>
                <span>{Math.round(progress)}%</span>
              </div>
              <Progress value={progress} />
            </div>
            <div className="flex items-center justify-center py-8">
              <Loader2 className="mr-2 h-6 w-6 animate-spin text-primary" />
              <span>Converting HTML to PDF documents...</span>
            </div>
          </div>
        )}
        
        {!isGenerating && generationResult && (
          <div className="space-y-6">
            <Alert variant={generationResult.errors.length === 0 ? "success" : "warning"}>
              <Check className="h-4 w-4" />
              <AlertTitle>PDF Generation Complete</AlertTitle>
              <AlertDescription>
                Generated {generationResult.num_files} PDF files in {generationResult.total_time.toFixed(2)} seconds
                {generationResult.errors.length > 0 && (
                  <>. <span className="font-semibold text-warning">Warning: {generationResult.errors.length} files had errors</span></>
                )}
              </AlertDescription>
            </Alert>
            
            <div>
              <h3 className="font-medium mb-2">Generation Summary</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="border rounded-md p-4">
                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Files Generated:</span>
                      <span className="font-medium">{generationResult.num_files}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Total Time:</span>
                      <span className="font-medium">{generationResult.total_time.toFixed(2)} seconds</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Average Time:</span>
                      <span className="font-medium">
                        {(generationResult.total_time / generationResult.num_files).toFixed(2)} seconds per file
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-muted-foreground">Errors:</span>
                      <span className="font-medium">{generationResult.errors.length}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div>
              <h3 className="font-medium mb-2">Generated PDF Files</h3>
              <div className="rounded-md border overflow-hidden">
                <div className="max-h-64 overflow-y-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-12">#</TableHead>
                        <TableHead>File Name</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {generationResult.pdf_files.slice(0, 10).map((fileName, index) => (
                        <TableRow key={index}>
                          <TableCell>{index + 1}</TableCell>
                          <TableCell className="font-mono text-xs">{fileName}</TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end space-x-2">
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => viewPdfFile(fileName)}
                              >
                                <ExternalLink className="h-4 w-4 mr-1" />
                                View
                              </Button>
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => downloadPdfFile(fileName)}
                              >
                                <Download className="h-4 w-4 mr-1" />
                                Download
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                      {generationResult.pdf_files.length > 10 && (
                        <TableRow>
                          <TableCell colSpan={3} className="text-center text-muted-foreground">
                            +{generationResult.pdf_files.length - 10} more files
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </div>
              </div>
            </div>
            
            {generationResult.errors.length > 0 && (
              <div>
                <h3 className="font-medium mb-2">Generation Errors</h3>
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>File</TableHead>
                        <TableHead>Error</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {generationResult.errors.map((error, index) => (
                        <TableRow key={index}>
                          <TableCell>{error.file}</TableCell>
                          <TableCell>{error.error}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
      <CardFooter className="flex justify-between">
        <Button
          variant="outline"
          onClick={handleRetry}
          disabled={isGenerating}
        >
          Regenerate PDFs
        </Button>
        <Button
          onClick={handleComplete}
          disabled={isGenerating || !generationResult}
        >
          Complete & View All
        </Button>
      </CardFooter>
    </Card>
  );
};

export default PdfGenerationStep;
```

## C:\xampp\htdocs\DocTypeGen\public\src\components\workflow\StorageStep.tsx
```tsx
// src/components/workflow/StorageStep.tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { commandService } from '@/api/services';
import { CommandResponse } from '@/types';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Spinner } from '@/components/ui/spinner';
import { AlertCircle, CheckCircle, Cloud, Upload } from 'lucide-react';
import { toast } from '@/components/ui/use-toast';

interface StorageStepProps {
  onComplete: (result: CommandResponse) => void;
}

const StorageStep: React.FC<StorageStepProps> = ({ onComplete }) => {
  const navigate = useNavigate();
  
  const [isTransferring, setIsTransferring] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [transferResult, setTransferResult] = useState<any>(null);
  const [progress, setProgress] = useState(0);
  
  const simulateProgress = () => {
    setProgress(0);
    const interval = setInterval(() => {
      setProgress(prev => {
        const newProgress = prev + Math.random() * 10;
        if (newProgress >= 100) {
          clearInterval(interval);
          return 100;
        }
        return newProgress;
      });
    }, 300);
    return interval;
  };
  
  const handleTransfer = async () => {
    setIsTransferring(true);
    setError(null);
    
    // Start progress simulation
    const progressInterval = simulateProgress();
    
    try {
      const result = await commandService.transferToS3();
      setTransferResult(result);
      
      // Ensure progress shows 100% when complete
      setProgress(100);
      
      if (result.success) {
        setIsComplete(true);
        toast({
          title: 'Transfer Complete',
          description: 'Successfully transferred to S3 storage',
          duration: 3000
        });
      } else {
        setError(result.error || 'Failed to transfer to S3 storage');
      }
    } catch (err: any) {
      console.error('Error transferring to S3 storage:', err);
      setError(err.message || 'Failed to transfer to S3 storage');
    } finally {
      setIsTransferring(false);
      clearInterval(progressInterval);
    }
  };
  
  const goBack = () => {
    navigate('/workflow/sync');
  };
  
  const goNext = () => {
    navigate('/workflow/complete');
    
    // Call onComplete with a success result
    onComplete({
      success: true,
      command: 'transfer_to_s3',
      result: transferResult || { status: 'success', message: 'Transfer to S3 storage completed' }
    });
  };
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Storage</CardTitle>
        <CardDescription>Transfer documents and logs to S3 storage</CardDescription>
      </CardHeader>
      
      <CardContent>
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        <div className="text-center py-12">
          {isComplete ? (
            <>
              <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2">Transfer Complete</h3>
              <p className="text-muted-foreground mb-6">
                All documents and logs have been successfully transferred to S3 storage.
              </p>
            </>
          ) : (
            <>
              <Cloud className="h-16 w-16 text-blue-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2">Transfer to S3 Storage</h3>
              <p className="text-muted-foreground mb-6">
                This step will transfer all generated documents, logs, and session data to S3 storage
                for long-term archival and access.
              </p>
              
              {isTransferring && (
                <div className="w-full max-w-md mx-auto mb-4">
                  <div className="relative pt-1">
                    <div className="text-right mb-1 text-xs text-muted-foreground">
                      {Math.round(progress)}%
                    </div>
                    <div className="overflow-hidden h-2 text-xs flex rounded bg-muted">
                      <div 
                        style={{ width: `${progress}%` }}
                        className="shadow-none flex flex-col text-center whitespace-nowrap justify-center bg-blue-500"
                      />
                    </div>
                  </div>
                </div>
              )}
              
              <Button 
                onClick={handleTransfer}
                disabled={isTransferring}
                size="lg"
                className="mx-auto"
              >
                {isTransferring ? (
                  <>
                    <Spinner className="mr-2 h-4 w-4" />
                    Transferring...
                  </>
                ) : (
                  <>
                    <Upload className="mr-2 h-4 w-4" />
                    Transfer to S3
                  </>
                )}
              </Button>
            </>
          )}
        </div>
      </CardContent>
      
      <CardFooter className="flex justify-between">
        <Button variant="outline" onClick={goBack}>Back</Button>
        <Button onClick={goNext} disabled={!isComplete}>
          Next: Complete
        </Button>
      </CardFooter>
    </Card>
  );
};

export default StorageStep;

```

## C:\xampp\htdocs\DocTypeGen\public\src\components\workflow\SyncStep.tsx
```tsx
// src/components/workflow/SyncStep.tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { commandService } from '@/api/services';
import { CommandResponse } from '@/types';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Spinner } from '@/components/ui/spinner';
import { AlertCircle, CheckCircle, Database, HardDrive } from 'lucide-react';
import { toast } from '@/components/ui/use-toast';

interface SyncStepProps {
  onComplete: (result: CommandResponse) => void;
}

const SyncStep: React.FC<SyncStepProps> = ({ onComplete }) => {
  const navigate = useNavigate();
  
  const [isSyncing, setIsSyncing] = useState(false);
  const [isComplete, setIsComplete] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [syncResult, setSyncResult] = useState<any>(null);
  
  const handleSync = async () => {
    setIsSyncing(true);
    setError(null);
    
    try {
      const result = await commandService.syncToTenantDb();
      setSyncResult(result);
      
      if (result.success) {
        setIsComplete(true);
        toast({
          title: 'Sync Complete',
          description: 'Successfully synced to tenant database',
          duration: 3000
        });
      } else {
        setError(result.error || 'Failed to sync to tenant database');
      }
    } catch (err: any) {
      console.error('Error syncing to tenant database:', err);
      setError(err.message || 'Failed to sync to tenant database');
    } finally {
      setIsSyncing(false);
    }
  };
  
  const goBack = () => {
    navigate('/workflow/entity-creation');
  };
  
  const goNext = () => {
    navigate('/workflow/storage');
    
    // Call onComplete with a success result
    onComplete({
      success: true,
      command: 'sync_tenant_db',
      result: syncResult || { status: 'success', message: 'Sync to tenant database completed' }
    });
  };
  
  return (
    <Card>
      <CardHeader>
        <CardTitle>Data Sync</CardTitle>
        <CardDescription>Sync processed documents to tenant database</CardDescription>
      </CardHeader>
      
      <CardContent>
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}
        
        <div className="text-center py-12">
          {isComplete ? (
            <>
              <CheckCircle className="h-16 w-16 text-green-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2">Sync Complete</h3>
              <p className="text-muted-foreground mb-6">
                All documents have been successfully synced to the tenant database.
              </p>
            </>
          ) : (
            <>
              <Database className="h-16 w-16 text-blue-500 mx-auto mb-4" />
              <h3 className="text-lg font-medium mb-2">Sync to Tenant Database</h3>
              <p className="text-muted-foreground mb-6">
                This step will synchronize all processed documents to the tenant database.
                This includes all generated documents, lookups, and entity relationships.
              </p>
              
              <Button 
                onClick={handleSync}
                disabled={isSyncing}
                size="lg"
                className="mx-auto"
              >
                {isSyncing ? (
                  <>
                    <Spinner className="mr-2 h-4 w-4" />
                    Syncing...
                  </>
                ) : (
                  <>
                    <Database className="mr-2 h-4 w-4" />
                    Sync to Database
                  </>
                )}
              </Button>
            </>
          )}
        </div>
      </CardContent>
      
      <CardFooter className="flex justify-between">
        <Button variant="outline" onClick={goBack}>Back</Button>
        <Button onClick={goNext} disabled={!isComplete}>
          Next: Storage
        </Button>
      </CardFooter>
    </Card>
  );
};

export default SyncStep;

```

## C:\xampp\htdocs\DocTypeGen\public\src\components\workflow\ValidateStep.tsx
```tsx
// src/components/workflow/ValidateStep.tsx
import { useState, useEffect } from 'react';
import { useQuery, useMutation } from '@tanstack/react-query';
import { toast } from 'sonner';
import { ArrowRight, CheckCircle, XCircle, Loader2, AlertTriangle, Edit, Pencil, Save, RotateCcw, FileCode, Info, RefreshCw, Trash2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { commandService } from '@/api/services';
import { CommandResponse, ValidationResult } from '@/types';

// Import our utility modules
import { 
  ValidationRowData, 
  ValidationFieldMatch, 
  SchemaFieldInfo, 
  SchemaValidationType, 
  MappingStructure, 
  getValidationTypeColor 
} from '@/utils/validationTypes';
import { 
  getFieldValidationInfo, 
  processSchemaInfo, 
  extractAvailableColumns 
} from '@/utils/validationHelpers';
import { 
  prepareMappingUpdates, 
  updateFieldMapping 
} from '@/utils/mappingUtils';

interface ValidateStepProps {
    onComplete: (result: CommandResponse) => void;
}

export const ValidateStep: React.FC<ValidateStepProps> = ({ onComplete }) => {
    const [isValidating, setIsValidating] = useState(false);
    const [validationResults, setValidationResults] = useState<ValidationResult | null>(null);
    const [fieldMatches, setFieldMatches] = useState<MappingStructure | null>(null);
    const [originalFieldMatches, setOriginalFieldMatches] = useState<MappingStructure | null>(null);
    const [editMode, setEditMode] = useState(false);
    const [activeTab, setActiveTab] = useState('fields');
    const [rowErrors, setRowErrors] = useState<ValidationRowData[]>([]);
    const [isAdjustingMapping, setIsAdjustingMapping] = useState(false);
    const [availableColumns, setAvailableColumns] = useState<string[]>([]);
    const [currentEditField, setCurrentEditField] = useState<{field: string, match: ValidationFieldMatch} | null>(null);
    const [schemaInfo, setSchemaInfo] = useState<any>(null);
    const [schemaFields, setSchemaFields] = useState<SchemaFieldInfo[]>([]);
    const [validationTypes, setValidationTypes] = useState<Record<string, SchemaValidationType>>({});
    const [allValidationTypes, setAllValidationTypes] = useState<Record<string, {description: string, details: any}>>({});
    const [passThreshold, setPassThreshold] = useState(80); // Default, will be updated from schema
    const [isResetConfirmOpen, setIsResetConfirmOpen] = useState(false);

    // We'll assume mapping exists for now; in a future update we could add a real check
    const hasMappingData = fieldMatches && Object.keys(fieldMatches).length > 0;

    const validateMutation = useMutation({
        mutationFn: () => commandService.validateData(),
        onSuccess: (data: any) => {
            if (data) {
                const validationData = data.validation_results || data;
                setValidationResults(validationData);
                setFieldMatches(data.field_matches || {});
                setOriginalFieldMatches(JSON.parse(JSON.stringify(data.field_matches || {})));
                
                // Store the full schema info
                if (data.schema) {
                    const schema = data.schema;
                    setSchemaInfo(schema);
                    
                    // Process schema data using our utility function
                    const { 
                        schemaFields: fields, 
                        validationTypes: types,
                        allValidationTypes: allTypes,
                        passThreshold: threshold
                    } = processSchemaInfo(schema);
                    
                    setSchemaFields(fields);
                    setValidationTypes(types);
                    setAllValidationTypes(allTypes);
                    setPassThreshold(threshold);
                }
                
                // Handle row validations if available
                const rowValidations = data.row_validations || [];
                setRowErrors(rowValidations.filter((row: ValidationRowData) => !row.valid));
                
                // Extract available columns from the validation results
                setAvailableColumns(extractAvailableColumns(rowValidations));
                
                toast.success('Validation completed');
            } else {
                toast.error('Validation returned unexpected result');
            }
            setIsValidating(false);
        },
        onError: (error: unknown) => {
            console.error('Validation error:', error);
            toast.error('Failed to validate data');
            setIsValidating(false);
        },
    });

    const updateMappingMutation = useMutation({
        mutationFn: (updatedMapping: Record<string, string>) => 
            commandService.updateMapping(updatedMapping),
        onSuccess: (data: any) => {
            if (data) {
                toast.success('Mapping updated successfully');
                // Update state with the mapping results
                if (data.validation_results) {
                    setValidationResults(data.validation_results);
                }
                if (data.field_matches) {
                    setFieldMatches(data.field_matches);
                    setOriginalFieldMatches(JSON.parse(JSON.stringify(data.field_matches)));
                }
                if (data.row_validations) {
                    setRowErrors(data.row_validations.filter((row: ValidationRowData) => !row.valid));
                }
                
                // Update schema info if provided
                if (data.schema) {
                    setSchemaInfo(data.schema);
                }
            } else {
                toast.error('Mapping update returned unexpected result');
            }
            setEditMode(false);
            setIsAdjustingMapping(false);
        },
        onError: (error: unknown) => {
            console.error('Mapping update error:', error);
            toast.error('Failed to update mapping');
            setIsAdjustingMapping(false);
        },
    });

    const handleValidate = () => {
        setIsValidating(true);
        validateMutation.mutate();
    };

    const handleSaveMapping = () => {
        if (!fieldMatches || !originalFieldMatches) return;
        
        setIsAdjustingMapping(true);
        
        // Use our utility function to prepare the mapping updates
        const updateData = prepareMappingUpdates(fieldMatches, originalFieldMatches);
        
        // Only send the update if there are changes
        if (Object.keys(updateData).length > 0) {
            updateMappingMutation.mutate(updateData);
        } else {
            setEditMode(false);
            setIsAdjustingMapping(false);
            toast.info('No changes to save');
        }
    };

    const handleResetMapping = () => {
        if (originalFieldMatches) {
            setFieldMatches(JSON.parse(JSON.stringify(originalFieldMatches)));
            setEditMode(false);
        }
    };

    const handleUpdateFieldMatch = (typeName: string, columnName: string) => {
        if (!fieldMatches) return;
        
        // Use our utility function to update the field mapping
        const updatedMapping = updateFieldMapping(fieldMatches, typeName, columnName);
        setFieldMatches(updatedMapping);
        setCurrentEditField(null);
    };
    
    const handleUpdateFieldType = (fieldName: string, dataType: string) => {
        if (!fieldMatches) return;
        
        setFieldMatches(prev => {
            if (!prev) return prev;
            
            return {
                ...prev,
                [fieldName]: {
                    ...prev[fieldName],
                    data_type: dataType
                }
            };
        });
    };
    
    // Select a schema field for the current column being mapped
    const handleSelectSchemaField = (schemaFieldName: string) => {
        if (!currentEditField || !schemaInfo?.schema?.[schemaFieldName]) return;
        
        const schemaField = schemaInfo.schema[schemaFieldName];
        
        setFieldMatches(prev => {
            if (!prev) return prev;
            
            return {
                ...prev,
                [currentEditField.field]: {
                    ...prev[currentEditField.field],
                    field: schemaFieldName,
                    data_type: schemaField.validate_type,
                    required: !!schemaField.required,
                    status: 'matched'
                }
            };
        });
    };
    
    /**
     * Get information about a field from the validation types
     */
    const getFieldInfo = (fieldName: string) => {
        if (!validationTypes[fieldName]) return "";
        
        const fieldInfo = validationTypes[fieldName] as any;
        const details = fieldInfo;
        
        let infoText = fieldInfo.description || "";
        
        if (fieldInfo.required !== undefined) {
            infoText += ` Required: ${fieldInfo.required ? 'Yes' : 'No'}.`;
        }
        
        if (fieldInfo.validate_type) {
            switch (fieldInfo.validate_type) {
                case 'REGEX':
                    infoText += ` Pattern: ${fieldInfo.regex || 'N/A'}`;
                    break;
                case 'LEV_DISTANCE':
                    infoText += ` List: ${fieldInfo.list || 'N/A'}, Distance: ${fieldInfo.distance || 'N/A'}`;
                    break;
                case 'ENUM':
                    infoText += ` Allowed values: ${fieldInfo.enum ? JSON.stringify(fieldInfo.enum) : 'N/A'}`;
                    break;
            }
        }
        
        return infoText;
    };

    // Get validation type badge color based on type
    const getValidationTypeColor = (type: string): string => {
        switch (type) {
            case 'REGEX': return 'bg-gray-500';
            case 'LEV_DISTANCE': return 'bg-gray-500';
            case 'SA_ID_NUMBER': return 'bg-gray-500';
            case 'BANK_ACCOUNT_NUMBER': return 'bg-gray-500';
            case 'DECIMAL_AMOUNT': return 'bg-gray-500';
            case 'UNIX_DATE': return 'bg-gray-500';
            case 'ENUM': return 'bg-gray-500';
            default: return 'bg-gray-500';
        }
    };

    // Function to reset/regenerate mappings
    const resetMappings = async () => {
        try {
            setIsValidating(true);
            // First delete the existing mapping
            await commandService.deleteMapping();
            toast.success("Mapping file deleted successfully");
            
            // Then generate a new mapping
            await commandService.generateMapping();
            
            // Refresh validation with the new mapping
            await validateMutation.mutateAsync();
            
            toast.success("Mappings have been regenerated");
        } catch (error) {
            console.error("Error resetting mappings:", error);
            toast.error("Failed to reset mappings");
        } finally {
            setIsValidating(false);
            setIsResetConfirmOpen(false);
        }
    };

    useEffect(() => {
        console.log("VALIDATION TYPES:", JSON.stringify(validationTypes, null, 2));
    }, []);

    if (isValidating || validateMutation.isPending) {
        return (
            <div className="flex flex-col items-center justify-center py-8 space-y-4">
                <Loader2 className="h-12 w-12 animate-spin text-gray-500" />
                <h3 className="text-lg font-medium">Validating data...</h3>
                <p className="text-center text-muted-foreground max-w-md">
                    The system is analyzing your data, detecting document type, and validating fields.
                </p>
                <Progress value={30} className="w-64 h-2" />
            </div>
        );
    }

    if (validationResults) {
        const { document_type, match_score, valid_rows, invalid_rows, total_rows, success_rate } = validationResults;

        // Determine severity based on success rate
        let severity: 'success' | 'warning' | 'error' = 'success';
        if (success_rate < 80) {
            severity = 'error';
        } else if (success_rate < 95) {
            severity = 'warning';
        }
        
        const canProceedToNextStep = success_rate >= passThreshold && !editMode;

        return (
            <div className="space-y-6">
                {/* Document type detection alert */}
                <Alert>
                    <CheckCircle className="h-4 w-4" />
                    <AlertTitle>Document Type Detection</AlertTitle>
                    <AlertDescription>
                        Document type detected: <Badge className="ml-1">{document_type}</Badge> with {(match_score || 0).toFixed(1)}% match confidence
                    </AlertDescription>
                </Alert>

                {/* Stats overview */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div className="bg-card border rounded-lg p-4 text-center">
                        <h4 className="text-sm font-medium">Total Rows</h4>
                        <p className="text-2xl font-bold">{total_rows}</p>
                    </div>
                    <div className="bg-card border rounded-lg p-4 text-center">
                        <h4 className="text-sm font-medium">Valid Rows</h4>
                        <p className="text-2xl font-bold text-gray-500">{valid_rows}</p>
                    </div>
                    <div className="bg-card border rounded-lg p-4 text-center">
                        <h4 className="text-sm font-medium">Invalid Rows</h4>
                        <p className="text-2xl font-bold text-gray-500">{invalid_rows}</p>
                    </div>
                </div>

                {/* Success rate progress */}
                <div>
                    <div className="flex justify-between mb-2">
                        <span className="text-sm font-medium">Success Rate</span>
                        <span className="text-sm font-medium">{(success_rate || 0).toFixed(1)}%</span>
                    </div>
                    <Progress
                        value={success_rate || 0}
                        className="h-3"
                        indicatorClassName={
                            success_rate >= 95 ? "bg-gray-500" :
                                success_rate >= passThreshold ? "bg-gray-500" :
                                    "bg-gray-500"
                        }
                    />
                    <div className="flex justify-end mt-1">
                        <span className="text-xs text-muted-foreground">Minimum threshold: {passThreshold}%</span>
                    </div>
                </div>

                <Separator />

                {/* Tabs for field mapping and row errors */}
                <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
                    <TabsList className="grid grid-cols-2 mb-4">
                        <TabsTrigger value="fields">Field Mapping</TabsTrigger>
                        <TabsTrigger value="errors">Validation Errors</TabsTrigger>
                    </TabsList>

                    {/* Field matches tab */}
                    <TabsContent value="fields" className="space-y-6">
                        <div className="flex justify-between items-center">
                            <h3 className="text-lg font-medium">Field Mapping</h3>
                            <div className="space-x-2">
                                {editMode ? (
                                    <>
                                        <Button 
                                            variant="outline" 
                                            size="sm" 
                                            onClick={handleResetMapping}
                                            disabled={isAdjustingMapping}
                                        >
                                            <RotateCcw className="h-4 w-4 mr-1" /> Cancel
                                        </Button>
                                        <Button 
                                            variant="default" 
                                            size="sm" 
                                            onClick={handleSaveMapping}
                                            disabled={isAdjustingMapping}
                                        >
                                            {isAdjustingMapping ? (
                                                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
                                            ) : (
                                                <Save className="h-4 w-4 mr-1" />
                                            )}
                                            Save Mapping
                                        </Button>
                                    </>
                                ) : (
                                    hasMappingData && (
                                        <Button 
                                            variant="outline" 
                                            size="sm" 
                                            onClick={() => setEditMode(true)}
                                        >
                                            <Pencil className="h-4 w-4 mr-1" /> Edit Mapping
                                        </Button>
                                    )
                                )}
                            </div>
                        </div>

                        <div className="border rounded-lg overflow-hidden">
                            <table className="w-full text-sm">
                                <thead className="bg-muted">
                                    <tr>
                                        <th className="text-left p-3 font-medium">Column Name</th>
                                        <th className="text-left p-3 font-medium">Matched Type</th>
                                        <th className="text-left p-3 font-medium">Validation Type</th>
                                        {editMode && <th className="text-center p-3 font-medium">Action</th>}
                                    </tr>
                                </thead>
                                <tbody className="divide-y">
                                    {fieldMatches && Object.entries(fieldMatches).map(([columnName, typeInfo]) => {
                                        // Simplified approach - just display basic information
                                        const typeName = typeof typeInfo.type === 'string' ? typeInfo.type : 'Unknown';
                                        const validationType = typeof typeInfo.validation === 'string' ? typeInfo.validation : 
                                                             validationTypes[typeName]?.type || "string";
                                        
                                        return (
                                            <tr key={columnName} className="hover:bg-muted/50">
                                                <td className="p-3 font-medium">
                                                    {columnName}
                                                </td>
                                                <td className="p-3">
                                                    {typeName}
                                                </td>
                                                <td className="p-3">
                                                    {validationType}
                                                </td>
                                                {editMode && (
                                                    <td className="p-3 text-center">
                                                        <Button 
                                                            variant="ghost" 
                                                            size="sm"
                                                            onClick={() => setCurrentEditField({
                                                                field: typeName, 
                                                                match: {
                                                                    column: columnName,
                                                                    field: typeName,
                                                                    status: 'matched',
                                                                    required: !!(validationTypes[typeName] as any)?.required,
                                                                    data_type: validationType
                                                                }
                                                            })}
                                                        >
                                                            <Edit className="h-4 w-4" />
                                                        </Button>
                                                    </td>
                                                )}
                                            </tr>
                                        );
                                    })}
                                </tbody>
                            </table>
                        </div>
                    </TabsContent>

                    {/* Row errors tab - simplified to avoid rendering objects */}
                    <TabsContent value="errors" className="space-y-4">
                        <h3 className="text-lg font-medium">Validation Errors</h3>
                        {rowErrors.length > 0 ? (
                            <div className="border rounded-lg p-4">
                                <p>{rowErrors.length} rows have validation errors</p>
                                <p className="text-sm text-muted-foreground mt-2">
                                    Detailed error information is available but not displayed to avoid rendering issues.
                                </p>
                            </div>
                        ) : (
                            <Alert variant="success">
                                <CheckCircle className="h-4 w-4" />
                                <AlertTitle>All rows valid</AlertTitle>
                                <AlertDescription>
                                    All rows in your data have passed validation.
                                </AlertDescription>
                            </Alert>
                        )}
                    </TabsContent>
                </Tabs>

                {/* Actions */}
                <div className="flex justify-end items-center pt-4 gap-2">
                    <Button 
                        variant="outline" 
                        disabled={isValidating}
                        onClick={handleValidate} 
                        className="flex items-center"
                    >
                        {isValidating ? (
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        ) : (
                            <RefreshCw className="h-4 w-4 mr-2" />
                        )}
                        Re-validate Data
                    </Button>
                    
                    <Button 
                        variant="outline" 
                        disabled={isValidating}
                        onClick={() => setIsResetConfirmOpen(true)} 
                        className="flex items-center text-destructive hover:text-destructive"
                    >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Reset Mappings
                    </Button>
                    
                    <Button 
                        disabled={!canProceedToNextStep} 
                        onClick={() => onComplete({
                            success: true,
                            command: 'validate',
                            result: {
                                validation_results: validationResults,
                                field_matches: fieldMatches
                            }
                        })}
                    >
                        Continue <ArrowRight className="h-4 w-4 ml-2" />
                    </Button>
                </div>

                {/* Edit field dialog */}
                <Dialog open={!!currentEditField} onOpenChange={(open) => !open && setCurrentEditField(null)}>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Edit Field Type</DialogTitle>
                            <DialogDescription>
                                Select a field type for column "{currentEditField?.match.column}"
                            </DialogDescription>
                        </DialogHeader>
                        
                        {currentEditField && (
                            <div className="space-y-4 py-2">
                                <div className="grid gap-2">
                                    <Label htmlFor="type">Field Type</Label>
                                    
                                    {/* Simple table of all available types */}
                                    <div className="border rounded-md overflow-auto max-h-[400px] bg-gray-800 text-white">
                                        {/* None option */}
                                        <div 
                                            className="p-3 cursor-pointer hover:bg-black border-b border-gray-700"
                                            onClick={() => {
                                                setCurrentEditField({
                                                    ...currentEditField,
                                                    field: "",
                                                    match: {
                                                        ...currentEditField.match,
                                                        field: ""
                                                    }
                                                });
                                            }}
                                        >
                                            <span className="text-gray-300">None (unmapped)</span>
                                        </div>
                                        
                                        {/* Table of all available types */}
                                        <table className="w-full">
                                            <tbody>
                                                {Object.entries(validationTypes).map(([type, typeObj]) => (
                                                    <tr
                                                        key={String(type)}
                                                        className={`border-b border-gray-700 ${
                                                            currentEditField?.field === type ? 'bg-black' : 'bg-gray-800'
                                                        } hover:bg-black`}
                                                        onClick={() => {
                                                            setCurrentEditField({
                                                                ...currentEditField,
                                                                field: type,
                                                                match: {
                                                                    ...currentEditField.match,
                                                                    field: type,
                                                                },
                                                            });
                                                        }}
                                                    >
                                                        <td className="p-3">
                                                            {/* Type name */}
                                                            <div className="font-bold text-md mb-1">{String(type)}</div>

                                                            {/* Display all keys and values as strings */}
                                                            <div className="pl-2 space-y-1 text-sm text-gray-300">
                                                                {Object.entries(typeObj).map(([key, value]) => (
                                                                    <div key={key}>
                                                                        <b>{key}:</b> {String(typeof value === 'object' ? JSON.stringify(value) : value)}
                                                                    </div>
                                                                ))}
                                                            </div>
                                                        </td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        )}
                        
                        <DialogFooter>
                            <Button variant="outline" onClick={() => setCurrentEditField(null)}>
                                Cancel
                            </Button>
                            <Button onClick={() => {
                                if (currentEditField) {
                                    handleUpdateFieldMatch(currentEditField.field, currentEditField.match.column);
                                    setCurrentEditField(null);
                                }
                            }}>Save</Button>
                        </DialogFooter>
                    </DialogContent>
                </Dialog>
                
                {/* Reset Mappings Confirmation Dialog */}
                <Dialog open={isResetConfirmOpen} onOpenChange={setIsResetConfirmOpen}>
                    <DialogContent>
                        <DialogHeader>
                            <DialogTitle>Reset Field Mappings</DialogTitle>
                            <DialogDescription>
                                This will delete your current field mappings and generate new ones. 
                                A backup of your current mappings will be created.
                                This action cannot be undone.
                            </DialogDescription>
                        </DialogHeader>
                        <div className="flex justify-end gap-3 mt-4">
                            <Button variant="outline" onClick={() => setIsResetConfirmOpen(false)}>
                                Cancel
                            </Button>
                            <Button variant="destructive" onClick={resetMappings}>
                                {isValidating ? 
                                    <Loader2 className="h-4 w-4 mr-2 animate-spin" /> : 
                                    <Trash2 className="h-4 w-4 mr-2" />
                                }
                                Reset Mappings
                            </Button>
                        </div>
                    </DialogContent>
                </Dialog>
            </div>
        );
    }

    // Initial state
    return (
        <div className="space-y-6">
            <div className="text-center py-12">
                <h3 className="text-xl font-medium mb-4">Validate Your Data</h3>
                <p className="text-muted-foreground mb-6 max-w-md mx-auto">
                    Click the button below to validate your data. The system will detect the document type
                    and validate your data against the schema requirements.
                </p>
                <Button onClick={handleValidate} disabled={isValidating} size="lg">
                    {isValidating ? (
                        <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Validating...
                        </>
                    ) : (
                        'Start Validation'
                    )}
                </Button>
            </div>
        </div>
    );
}

export default ValidateStep;
```

## C:\xampp\htdocs\DocTypeGen\public\src\components\workflow\WorkflowStepper.tsx
```tsx
// src/components/workflow/WorkflowStepper.tsx
import React from 'react';
import { Check, X } from 'lucide-react';
import { cn } from "@/lib/utils";

interface WorkflowStepperProps {
  activeStep: number;
}

interface Step {
  id: number;
  name: string;
  description: string;
  optional?: boolean;
}

const WorkflowStepper: React.FC<WorkflowStepperProps> = ({ activeStep }) => {
  const steps: Step[] = [
    {
      id: 0,
      name: 'Import',
      description: 'Upload CSV or Excel file',
    },
    {
      id: 1,
      name: 'Validate',
      description: 'Validate data format and structure',
    },
    {
      id: 2,
      name: 'Map',
      description: 'Map fields to document template',
    },
    {
      id: 3,
      name: 'HTML',
      description: 'Generate HTML documents',
    },
    {
      id: 4,
      name: 'PDF',
      description: 'Generate PDF documents',
      optional: true,
    },
    {
      id: 5,
      name: 'Lookups',
      description: 'Resolve lookups against external data',
    },
    {
      id: 6,
      name: 'Entity Creation',
      description: 'Create missing entities',
      optional: true,
    },
    {
      id: 7,
      name: 'Data Sync',
      description: 'Sync to tenant database',
      optional: true,
    },
    {
      id: 8,
      name: 'Storage',
      description: 'Move to S3 storage',
      optional: true,
    },
    {
      id: 9,
      name: 'Complete',
      description: 'Processing complete',
    },
  ];

  return (
    <div className="w-full">
      <div className="hidden md:flex">
        <div className="w-full flex items-center">
          {steps.map((step, index) => (
            <React.Fragment key={step.id}>
              {/* Step indicator */}
              <div className="relative flex flex-col items-center">
                <div
                  className={cn(
                    "w-10 h-10 flex items-center justify-center rounded-full border-2 transition-colors relative z-10",
                    activeStep > step.id
                      ? "bg-primary border-primary text-primary-foreground"
                      : activeStep === step.id
                      ? "border-primary text-primary"
                      : "border-muted-foreground text-muted-foreground"
                  )}
                >
                  {activeStep > step.id ? (
                    <Check className="w-5 h-5" />
                  ) : (
                    <span>{step.id + 1}</span>
                  )}
                </div>
                <div className="mt-2 text-center">
                  <div
                    className={cn(
                      "text-sm font-medium",
                      activeStep >= step.id
                        ? "text-foreground"
                        : "text-muted-foreground"
                    )}
                  >
                    {step.name}
                  </div>
                  <div className="text-xs text-muted-foreground hidden lg:block">
                    {step.description}
                  </div>
                </div>
              </div>
              
              {/* Connector line */}
              {index < steps.length - 1 && (
                <div
                  className={cn(
                    "flex-1 border-t-2 transition-colors",
                    activeStep > step.id
                      ? "border-primary"
                      : "border-muted-foreground/30"
                  )}
                />
              )}
            </React.Fragment>
          ))}
        </div>
      </div>
      
      {/* Mobile view - just show current step */}
      <div className="md:hidden">
        {steps[activeStep] && (
          <div className="flex items-center justify-center">
            <div
              className={cn(
                "w-10 h-10 flex items-center justify-center rounded-full border-2 border-primary text-primary"
              )}
            >
              <span>{activeStep + 1}</span>
            </div>
            <div className="ml-4">
              <div className="text-base font-medium">
                {steps[activeStep].name}
              </div>
              <div className="text-sm text-muted-foreground">
                {steps[activeStep].description}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkflowStepper;
```

## C:\xampp\htdocs\DocTypeGen\public\src\config\index.ts
```ts
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
```

## C:\xampp\htdocs\DocTypeGen\public\src\contexts\AuthContext.tsx
```tsx
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
```

## C:\xampp\htdocs\DocTypeGen\public\src\contexts\ThemeContext.tsx
```tsx
// src/contexts/ThemeContext.tsx
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
}

const ThemeContext = createContext<ThemeContextType>({} as ThemeContextType);

export const useTheme = () => useContext(ThemeContext);

interface ThemeProviderProps {
  children: ReactNode;
}

export const ThemeProvider: React.FC<ThemeProviderProps> = ({ children }) => {
  // Initialize theme from localStorage or system preference
  const [theme, setTheme] = useState<Theme>(() => {
    const savedTheme = localStorage.getItem('theme') as Theme;
    if (savedTheme) return savedTheme;
    
    // Use system preference as fallback
    return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
  });

  // Update document class and localStorage when theme changes
  useEffect(() => {
    const root = window.document.documentElement;
    
    // Remove previous theme class
    root.classList.remove('light', 'dark');
    
    // Add new theme class
    root.classList.add(theme);
    
    // Save to localStorage
    localStorage.setItem('theme', theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme(prevTheme => (prevTheme === 'light' ? 'dark' : 'light'));
  };

  return (
    <ThemeContext.Provider
      value={{
        theme,
        toggleTheme,
      }}
    >
      {children}
    </ThemeContext.Provider>
  );
};
```

## C:\xampp\htdocs\DocTypeGen\public\src\hooks\use-toast.ts
```ts
import * as React from "react"

import type {
  ToastActionElement,
  ToastProps,
} from "@/components/ui/toast"

const TOAST_LIMIT = 1
const TOAST_REMOVE_DELAY = 1000000

type ToasterToast = ToastProps & {
  id: string
  title?: React.ReactNode
  description?: React.ReactNode
  action?: ToastActionElement
}

const actionTypes = {
  ADD_TOAST: "ADD_TOAST",
  UPDATE_TOAST: "UPDATE_TOAST",
  DISMISS_TOAST: "DISMISS_TOAST",
  REMOVE_TOAST: "REMOVE_TOAST",
} as const

let count = 0

function genId() {
  count = (count + 1) % Number.MAX_SAFE_INTEGER
  return count.toString()
}

type ActionType = typeof actionTypes

type Action =
  | {
      type: ActionType["ADD_TOAST"]
      toast: ToasterToast
    }
  | {
      type: ActionType["UPDATE_TOAST"]
      toast: Partial<ToasterToast>
    }
  | {
      type: ActionType["DISMISS_TOAST"]
      toastId?: ToasterToast["id"]
    }
  | {
      type: ActionType["REMOVE_TOAST"]
      toastId?: ToasterToast["id"]
    }

interface State {
  toasts: ToasterToast[]
}

const toastTimeouts = new Map<string, ReturnType<typeof setTimeout>>()

const addToRemoveQueue = (toastId: string) => {
  if (toastTimeouts.has(toastId)) {
    return
  }

  const timeout = setTimeout(() => {
    toastTimeouts.delete(toastId)
    dispatch({
      type: "REMOVE_TOAST",
      toastId: toastId,
    })
  }, TOAST_REMOVE_DELAY)

  toastTimeouts.set(toastId, timeout)
}

export const reducer = (state: State, action: Action): State => {
  switch (action.type) {
    case "ADD_TOAST":
      return {
        ...state,
        toasts: [action.toast, ...state.toasts].slice(0, TOAST_LIMIT),
      }

    case "UPDATE_TOAST":
      return {
        ...state,
        toasts: state.toasts.map((t) =>
          t.id === action.toast.id ? { ...t, ...action.toast } : t
        ),
      }

    case "DISMISS_TOAST": {
      const { toastId } = action

      // ! Side effects ! - This could be extracted into a dismissToast() action,
      // but I'll keep it here for simplicity
      if (toastId) {
        addToRemoveQueue(toastId)
      } else {
        state.toasts.forEach((toast) => {
          addToRemoveQueue(toast.id)
        })
      }

      return {
        ...state,
        toasts: state.toasts.map((t) =>
          t.id === toastId || toastId === undefined
            ? {
                ...t,
                open: false,
              }
            : t
        ),
      }
    }
    case "REMOVE_TOAST":
      if (action.toastId === undefined) {
        return {
          ...state,
          toasts: [],
        }
      }
      return {
        ...state,
        toasts: state.toasts.filter((t) => t.id !== action.toastId),
      }
  }
}

const listeners: Array<(state: State) => void> = []

let memoryState: State = { toasts: [] }

function dispatch(action: Action) {
  memoryState = reducer(memoryState, action)
  listeners.forEach((listener) => {
    listener(memoryState)
  })
}

type Toast = Omit<ToasterToast, "id">

function toast({ ...props }: Toast) {
  const id = genId()

  const update = (props: ToasterToast) =>
    dispatch({
      type: "UPDATE_TOAST",
      toast: { ...props, id },
    })
  const dismiss = () => dispatch({ type: "DISMISS_TOAST", toastId: id })

  dispatch({
    type: "ADD_TOAST",
    toast: {
      ...props,
      id,
      open: true,
      onOpenChange: (open) => {
        if (!open) dismiss()
      },
    },
  })

  return {
    id: id,
    dismiss,
    update,
  }
}

function useToast() {
  const [state, setState] = React.useState<State>(memoryState)

  React.useEffect(() => {
    listeners.push(setState)
    return () => {
      const index = listeners.indexOf(setState)
      if (index > -1) {
        listeners.splice(index, 1)
      }
    }
  }, [state])

  return {
    ...state,
    toast,
    dismiss: (toastId?: string) => dispatch({ type: "DISMISS_TOAST", toastId }),
  }
}

export { useToast, toast }

```

## C:\xampp\htdocs\DocTypeGen\public\src\lib\utils.ts
```ts
import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

export function formatFileSize(bytes: number): string {
  if (isNaN(bytes) || bytes < 0) return '0 B';

  const units = ['B', 'KB', 'MB', 'GB', 'TB'];
  const exponent = Math.floor(Math.log10(bytes) / 3);
  const value = bytes / Math.pow(1024, exponent);

  return `${value.toFixed(2)} ${units[exponent]}`;
}
```

## C:\xampp\htdocs\DocTypeGen\public\src\main.tsx
```tsx
// src/main.tsx
import React from 'react';
import ReactDOM from 'react-dom/client';
import App from './App';
import './index.css';

// Mount the application
ReactDOM.createRoot(document.getElementById('root') as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);
```

## C:\xampp\htdocs\DocTypeGen\public\src\pages\DashboardPage.tsx
```tsx
// src/pages/DashboardPage.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Plus, FileInput, Workflow, FileText, File, ArrowRight } from 'lucide-react';
import { sessionService, commandService } from "@/api/services";
import { Session, SessionStatus } from "@/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { useAuth } from "@/contexts/AuthContext";
import { Spinner } from "@/components/ui/spinner";
import ErrorWithHelper from "@/components/ui/ErrorWithHelper";

const DashboardPage: React.FC = () => {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [activeSession, setActiveSession] = useState<SessionStatus | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch sessions and active session on mount
  useEffect(() => {
    const fetchData = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        // Get active session
        const statusResponse = await commandService.getStatus();
        setActiveSession(statusResponse);
        
        // Get all sessions
        const logResponse = await sessionService.getLogs();
        setSessions(logResponse);
      } catch (err) {
        console.error('Error fetching dashboard data:', err);
        setError('Failed to load dashboard data. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchData();
  }, []);
  
  // Handle new session creation
  const handleNewSession = () => {
    navigate('/app/workflow/upload');
  };
  
  // Handle continue with active session
  const handleContinueSession = () => {
    if (activeSession?.session_hash) {
      navigate(`/app/workflow?session=${activeSession.session_hash}`);
    }
  };
  
  // Cards to display in the dashboard
  const dashboardCards = [
    {
      title: 'Upload Document',
      description: 'Import a CSV or Excel file to start processing',
      icon: FileInput,
      route: '/app/workflow/upload',
      footer: 'Start by uploading a file',
    },
    {
      title: 'Processing Workflow',
      description: 'Validate, map, and generate documents',
      icon: Workflow,
      route: '/app/workflow',
      footer: 'Step-by-step document generation',
    },
    {
      title: 'View Sessions',
      description: 'Browse all processing sessions',
      icon: File,
      route: '/app/sessions',
      footer: 'Manage existing sessions',
    },
    {
      title: 'Logs & Reports',
      description: 'View logs and generated reports',
      icon: FileText,
      route: '/app/logs',
      footer: 'Access logs and validation reports',
    },
  ];
  
  // Recent sessions to display (limit to 5)
  const recentSessions = sessions.slice(0, 5);

  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-8rem)] items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
        <Link to="/app/workflow/upload">
          <Button>
            <Plus className="mr-2 h-4 w-4" />
            New Session
          </Button>
        </Link>
      </div>
      
      {error && (
        <ErrorWithHelper message={error} helperKey="failedDashboardData" />
      )}
      
      {activeSession && activeSession.active_session && (
        <Card>
          <CardHeader>
            <CardTitle>Active Session</CardTitle>
            <CardDescription>
              You have an active processing session
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm">
              Session Hash: <span className="font-mono">{activeSession.session_hash}</span>
            </p>
          </CardContent>
          <CardFooter>
            <Link to={`/app/workflow?session=${activeSession.session_hash}`}>
              <Button className="w-full sm:w-auto">
                Continue Session
                <ArrowRight className="ml-2 h-4 w-4" />
              </Button>
            </Link>
          </CardFooter>
        </Card>
      )}
      
      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="recent">Recent Sessions</TabsTrigger>
        </TabsList>
        
        <TabsContent value="overview" className="space-y-4">
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {dashboardCards.map((card) => (
              <Card key={card.title} className="overflow-hidden">
                <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                  <CardTitle className="text-lg font-medium">
                    {card.title}
                  </CardTitle>
                  <card.icon className="h-4 w-4 text-muted-foreground" />
                </CardHeader>
                <CardContent>
                  <p className="text-sm text-muted-foreground">
                    {card.description}
                  </p>
                </CardContent>
                <CardFooter className="pt-0">
                  <Link to={card.route}>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      className="w-full"
                    >
                      {card.footer}
                    </Button>
                  </Link>
                </CardFooter>
              </Card>
            ))}
          </div>
          
          {user?.role === 'admin' && (
            <Card>
              <CardHeader>
                <CardTitle>Admin Controls</CardTitle>
                <CardDescription>
                  Administrative functions and settings
                </CardDescription>
              </CardHeader>
              <CardContent className="grid gap-4 md:grid-cols-2">
                <Link to="/app/users">
                  <Button 
                    variant="outline"
                  >
                    User Management
                  </Button>
                </Link>
                <Link to="/app/settings">
                  <Button 
                    variant="outline"
                  >
                    System Settings
                  </Button>
                </Link>
              </CardContent>
            </Card>
          )}
        </TabsContent>
        
        <TabsContent value="recent">
          <Card>
            <CardHeader>
              <CardTitle>Recent Sessions</CardTitle>
              <CardDescription>
                Your recent document processing sessions
              </CardDescription>
            </CardHeader>
            <CardContent>
              {recentSessions.length > 0 ? (
                <div className="space-y-4">
                  {recentSessions.map((session) => (
                    <div 
                      key={session.hash} 
                      className="flex items-center justify-between rounded-lg border p-4"
                    >
                      <div>
                        <p className="font-medium">
                          {session.name || `Session ${session.hash.substring(0, 8)}`}
                        </p>
                        <p className="text-sm text-muted-foreground">
                          {session.date}
                        </p>
                      </div>
                      <Link to={`/app/sessions/${session.hash}`}>
                        <Button 
                          variant="ghost"
                        >
                          View
                        </Button>
                      </Link>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-center text-muted-foreground py-8">
                  No recent sessions found. Start by uploading a new file.
                </p>
              )}
            </CardContent>
            <CardFooter>
              <Link to="/app/sessions">
                <Button 
                  variant="outline" 
                  className="w-full"
                >
                  View All Sessions
                </Button>
              </Link>
            </CardFooter>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default DashboardPage;
```

## C:\xampp\htdocs\DocTypeGen\public\src\pages\LoginPage.tsx
```tsx
// src/pages/LoginPage.tsx
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { z } from 'zod';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { useAuth } from "@/contexts/AuthContext";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";

// Define form schema
const formSchema = z.object({
  username: z.string().min(1, 'Username is required'),
  password: z.string().min(1, 'Password is required'),
});

type FormValues = z.infer<typeof formSchema>;

const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Initialize form
  const form = useForm<FormValues>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      username: '',
      password: '',
    },
  });

  // Handle form submission
  const onSubmit = async (values: FormValues) => {
    setError(null);
    setIsLoading(true);
    
    try {
      await login(values.username, values.password);
      navigate('/');
    } catch (err: any) {
      setError(err.response?.data?.error || 'Login failed. Please check your credentials.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-background p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1 text-center">
          <CardTitle className="text-2xl">Document Processing System</CardTitle>
          <CardDescription>
            Enter your credentials to sign in to your account
          </CardDescription>
        </CardHeader>
        <CardContent>
          {error && (
            <Alert variant="destructive" className="mb-4">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}
          
          <Form {...form}>
            <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
              <FormField
                control={form.control}
                name="username"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Username</FormLabel>
                    <FormControl>
                      <Input placeholder="Enter your username" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <FormField
                control={form.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Password</FormLabel>
                    <FormControl>
                      <Input type="password" placeholder="Enter your password" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <Button type="submit" className="w-full" disabled={isLoading}>
                {isLoading ? 'Signing in...' : 'Sign In'}
              </Button>
            </form>
          </Form>
        </CardContent>
        <CardFooter className="flex justify-center">
          <p className="text-xs text-muted-foreground">
            &copy; {new Date().getFullYear()} DocTypeGen | Digital Cabinet. All rights reserved.
          </p>
        </CardFooter>
      </Card>
    </div>
  );
};

export default LoginPage;
```

## C:\xampp\htdocs\DocTypeGen\public\src\pages\LogsPage.tsx
```tsx
// src/pages/LogsPage.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { FileText, Search, ExternalLink, ArrowLeft, File, Download, FileUp } from 'lucide-react';
import { sessionService } from "@/api/services";
import { LogDirectory, LogInfo } from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle } from 'lucide-react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";

const LogsListPage: React.FC = () => {
  const navigate = useNavigate();
  const [logs, setLogs] = useState<LogDirectory[]>([]);
  const [filteredLogs, setFilteredLogs] = useState<LogDirectory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  
  // Fetch logs on mount
  useEffect(() => {
    fetchLogs();
  }, []);
  
  // Filter logs when search term changes
  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredLogs(logs);
    } else {
      const term = searchTerm.toLowerCase();
      const filtered = logs.filter(
        log => 
          (log.name && log.name.toLowerCase().includes(term)) ||
          log.hash.toLowerCase().includes(term)
      );
      setFilteredLogs(filtered);
    }
  }, [searchTerm, logs]);
  
  const fetchLogs = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await sessionService.getLogs();
      setLogs(response);
      setFilteredLogs(response);
    } catch (err) {
      console.error('Error fetching logs:', err);
      setError('Failed to load logs. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };
  
  const handleViewLogs = (log: LogDirectory) => {
    navigate(`/app/logs/${log.hash}`);
  };
  
  // Function to format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-8rem)] items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Logs</h1>
      </div>
      
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      
      <div className="flex items-center space-x-2">
        <Search className="h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search logs..."
          value={searchTerm}
          onChange={handleSearch}
          className="w-full md:w-[300px]"
        />
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>All Logs</CardTitle>
          <CardDescription>
            View logs for all document processing sessions
          </CardDescription>
        </CardHeader>
        <CardContent>
          {filteredLogs.length > 0 ? (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Hash</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Files</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredLogs.map((log) => (
                    <TableRow key={log.hash}>
                      <TableCell className="font-medium">
                        {log.name || `Session ${log.hash.substring(0, 8)}`}
                      </TableCell>
                      <TableCell className="font-mono text-xs">
                        {log.hash.substring(0, 12)}...
                      </TableCell>
                      <TableCell>{formatDate(log.date)}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{log.file_count}</Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewLogs(log)}
                        >
                          <FileText className="mr-2 h-4 w-4" />
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <FileText className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="font-medium text-lg mb-1">No logs found</h3>
              <p className="text-muted-foreground mb-4">
                {searchTerm ? 'No logs match your search' : 'No processing sessions have been completed yet'}
              </p>
              {searchTerm ? (
                <Button variant="outline" onClick={() => setSearchTerm('')}>
                  Clear Search
                </Button>
              ) : (
                <Button onClick={() => navigate('/app/workflow/upload')}>
                  Start New Session
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

const LogDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [logInfo, setLogInfo] = useState<LogInfo | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState('html');
  
  // Fetch log details on mount
  useEffect(() => {
    if (id) {
      fetchLogDetails(id);
    }
  }, [id]);
  
  const fetchLogDetails = async (hash: string) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await sessionService.getLogInfo(hash);
      setLogInfo(response);
    } catch (err) {
      console.error('Error fetching log details:', err);
      setError('Failed to load log details. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleBackToList = () => {
    navigate('/app/logs');
  };
  
  const viewFile = (fileType: string, fileName: string) => {
    // Construct URL to file
    const baseUrl = window.location.origin;
    let path;
    
    if (fileType === 'log') {
      path = `${baseUrl}/static/${id}/www/${fileName}`;
    } else {
      path = `${baseUrl}/static/${id}/${fileType}/${fileName}`;
    }
    
    window.open(path, '_blank');
  };
  
  const downloadFile = (fileType: string, fileName: string) => {
    // Construct URL and trigger download
    const baseUrl = window.location.origin;
    let path;
    
    if (fileType === 'log') {
      path = `${baseUrl}/static/${id}/www/${fileName}`;
    } else {
      path = `${baseUrl}/static/${id}/${fileType}/${fileName}`;
    }
    
    const a = document.createElement('a');
    a.href = path;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  };
  
  const continueSession = () => {
    navigate(`/app/workflow?session=${id}`);
  };

  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-8rem)] items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error || !logInfo) {
    return (
      <div className="space-y-6">
        <Button variant="outline" onClick={handleBackToList}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Logs
        </Button>
        
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error || 'Log not found'}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center space-x-4">
        <Button variant="outline" onClick={handleBackToList}>
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Logs
        </Button>
        
        <Button onClick={continueSession}>
          <FileUp className="mr-2 h-4 w-4" />
          Continue Session
        </Button>
      </div>
      
      <div>
        <h1 className="text-3xl font-bold tracking-tight">
          {logInfo.name || `Session ${logInfo.hash.substring(0, 8)}`}
        </h1>
        <p className="text-muted-foreground">
          {logInfo.date} • Hash: <span className="font-mono">{logInfo.hash.substring(0, 16)}...</span>
        </p>
      </div>
      
      <Tabs defaultValue={activeTab} onValueChange={setActiveTab}>
        <TabsList>
          <TabsTrigger value="html">
            HTML Files ({logInfo.html_files.length})
          </TabsTrigger>
          <TabsTrigger value="pdf">
            PDF Files ({logInfo.pdf_files.length})
          </TabsTrigger>
          <TabsTrigger value="logs">
            Log Files ({logInfo.log_files.length})
          </TabsTrigger>
        </TabsList>
        
        <TabsContent value="html" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>HTML Files</CardTitle>
              <CardDescription>
                Generated HTML documents from this session
              </CardDescription>
            </CardHeader>
            <CardContent>
              {logInfo.html_files.length > 0 ? (
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-12">#</TableHead>
                        <TableHead>File Name</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {logInfo.html_files.map((fileName, index) => (
                        <TableRow key={index}>
                          <TableCell>{index + 1}</TableCell>
                          <TableCell className="font-mono text-xs">{fileName}</TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end space-x-2">
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => viewFile('html', fileName)}
                              >
                                <ExternalLink className="h-4 w-4 mr-1" />
                                View
                              </Button>
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => downloadFile('html', fileName)}
                              >
                                <Download className="h-4 w-4 mr-1" />
                                Download
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <File className="h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="font-medium mb-1">No HTML files</h3>
                  <p className="text-muted-foreground">
                    This session doesn't have any HTML files.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="pdf" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>PDF Files</CardTitle>
              <CardDescription>
                Generated PDF documents from this session
              </CardDescription>
            </CardHeader>
            <CardContent>
              {logInfo.pdf_files.length > 0 ? (
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-12">#</TableHead>
                        <TableHead>File Name</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {logInfo.pdf_files.map((fileName, index) => (
                        <TableRow key={index}>
                          <TableCell>{index + 1}</TableCell>
                          <TableCell className="font-mono text-xs">{fileName}</TableCell>
                          <TableCell className="text-right">
                            <div className="flex justify-end space-x-2">
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => viewFile('pdf', fileName)}
                              >
                                <ExternalLink className="h-4 w-4 mr-1" />
                                View
                              </Button>
                              <Button 
                                variant="ghost" 
                                size="sm"
                                onClick={() => downloadFile('pdf', fileName)}
                              >
                                <Download className="h-4 w-4 mr-1" />
                                Download
                              </Button>
                            </div>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <File className="h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="font-medium mb-1">No PDF files</h3>
                  <p className="text-muted-foreground">
                    This session doesn't have any PDF files.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="logs" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Log Files</CardTitle>
              <CardDescription>
                Processing logs and reports from this session
              </CardDescription>
            </CardHeader>
            <CardContent>
              {logInfo.log_files.length > 0 ? (
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead className="w-12">#</TableHead>
                        <TableHead>File Name</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {logInfo.log_files.map((fileName, index) => (
                        <TableRow key={index}>
                          <TableCell>{index + 1}</TableCell>
                          <TableCell className="font-mono text-xs">{fileName}</TableCell>
                          <TableCell className="text-right">
                            <Button 
                              variant="ghost" 
                              size="sm"
                              onClick={() => viewFile('log', fileName)}
                            >
                              <ExternalLink className="h-4 w-4 mr-1" />
                              View
                            </Button>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </div>
              ) : (
                <div className="flex flex-col items-center justify-center py-8 text-center">
                  <FileText className="h-12 w-12 text-muted-foreground mb-4" />
                  <h3 className="font-medium mb-1">No log files</h3>
                  <p className="text-muted-foreground">
                    This session doesn't have any log files.
                  </p>
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

// Export both components
export { LogsListPage, LogDetailPage };
```

## C:\xampp\htdocs\DocTypeGen\public\src\pages\SessionsPage.tsx
```tsx
// src/pages/SessionsPage.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Plus, Search, MoreHorizontal, Edit, FileText, FileUp } from 'lucide-react';
import { sessionService, commandService } from "@/api/services";
import { Session, SessionStatus } from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle } from 'lucide-react';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";

const SessionsPage: React.FC = () => {
  const navigate = useNavigate();
  const [sessions, setSessions] = useState<Session[]>([]);
  const [filteredSessions, setFilteredSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [activeSession, setActiveSession] = useState<SessionStatus | null>(null);
  
  // For rename dialog
  const [isRenameDialogOpen, setIsRenameDialogOpen] = useState(false);
  const [sessionToRename, setSessionToRename] = useState<Session | null>(null);
  const [newName, setNewName] = useState('');
  
  // Fetch sessions and active session on mount
  useEffect(() => {
    fetchSessions();
  }, []);
  
  // Filter sessions when search term changes
  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredSessions(sessions);
    } else {
      const term = searchTerm.toLowerCase();
      const filtered = sessions.filter(
        session => 
          (session.name && session.name.toLowerCase().includes(term)) ||
          session.hash.toLowerCase().includes(term) ||
          (session.document_type && session.document_type.toLowerCase().includes(term))
      );
      setFilteredSessions(filtered);
    }
  }, [searchTerm, sessions]);
  
  const fetchSessions = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      // Get active session
      const statusResponse = await commandService.getStatus();
      setActiveSession(statusResponse);
      
      // Get all sessions
      const logResponse = await sessionService.getLogs();
      setSessions(logResponse);
      setFilteredSessions(logResponse);
    } catch (err) {
      console.error('Error fetching sessions:', err);
      setError('Failed to load sessions. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };
  
  const handleNewSession = () => {
    navigate('/app/workflow/upload');
  };
  
  const handleOpenSession = (session: Session) => {
    navigate(`/app/workflow?session=${session.hash}`);
  };
  
  const handleViewLogs = (session: Session) => {
    navigate(`/app/logs/${session.hash}`);
  };
  
  const openRenameDialog = (session: Session) => {
    setSessionToRename(session);
    setNewName(session.name || '');
    setIsRenameDialogOpen(true);
  };
  
  const handleRename = async () => {
    if (!sessionToRename) return;
    
    try {
      await sessionService.renameLog(sessionToRename.hash, newName);
      
      // Update session in state
      setSessions(prevSessions => 
        prevSessions.map(session => 
          session.hash === sessionToRename.hash 
            ? { ...session, name: newName } 
            : session
        )
      );
      
      setIsRenameDialogOpen(false);
    } catch (err) {
      console.error('Error renaming session:', err);
      setError('Failed to rename session. Please try again.');
    }
  };
  
  // Function to format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return new Intl.DateTimeFormat('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    }).format(date);
  };

  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-8rem)] items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Sessions</h1>
        <Button onClick={handleNewSession}>
          <Plus className="mr-2 h-4 w-4" />
          New Session
        </Button>
      </div>
      
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      
      <div className="flex items-center space-x-2">
        <Search className="h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search sessions..."
          value={searchTerm}
          onChange={handleSearch}
          className="w-full md:w-[300px]"
        />
      </div>
      
      {activeSession && activeSession.active_session && (
        <Card>
          <CardHeader>
            <CardTitle>Active Session</CardTitle>
            <CardDescription>
              You have an active processing session
            </CardDescription>
          </CardHeader>
          <CardContent>
            <p className="text-sm">
              Session Hash: <span className="font-mono">{activeSession.session_hash}</span>
            </p>
          </CardContent>
          <CardFooter>
            <Button 
              onClick={() => navigate(`/app/workflow?session=${activeSession.session_hash}`)}
              className="w-full sm:w-auto"
            >
              Continue Processing
            </Button>
          </CardFooter>
        </Card>
      )}
      
      <Card>
        <CardHeader>
          <CardTitle>All Sessions</CardTitle>
          <CardDescription>
            Manage your document processing sessions
          </CardDescription>
        </CardHeader>
        <CardContent>
          {filteredSessions.length > 0 ? (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Name</TableHead>
                    <TableHead>Type</TableHead>
                    <TableHead>Date</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredSessions.map((session) => (
                    <TableRow key={session.hash}>
                      <TableCell className="font-medium">
                        {session.name || `Session ${session.hash.substring(0, 8)}`}
                      </TableCell>
                      <TableCell>
                        {session.document_type ? (
                          <Badge variant="outline">{session.document_type}</Badge>
                        ) : (
                          <span className="text-muted-foreground">Unknown</span>
                        )}
                      </TableCell>
                      <TableCell>{formatDate(session.date)}</TableCell>
                      <TableCell>
                        {session.hash === activeSession?.session_hash ? (
                          <Badge>Active</Badge>
                        ) : (
                          <Badge variant="outline">{session.last_operation || 'Completed'}</Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm">
                              <MoreHorizontal className="h-4 w-4" />
                              <span className="sr-only">Open menu</span>
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuLabel>Actions</DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem onClick={() => handleOpenSession(session)}>
                              <FileUp className="mr-2 h-4 w-4" />
                              Open in Workflow
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => handleViewLogs(session)}>
                              <FileText className="mr-2 h-4 w-4" />
                              View Logs
                            </DropdownMenuItem>
                            <DropdownMenuItem onClick={() => openRenameDialog(session)}>
                              <Edit className="mr-2 h-4 w-4" />
                              Rename
                            </DropdownMenuItem>
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <FileText className="h-12 w-12 text-muted-foreground mb-4" />
              <h3 className="font-medium text-lg mb-1">No sessions found</h3>
              <p className="text-muted-foreground mb-4">
                {searchTerm ? 'No sessions match your search' : 'You have not created any sessions yet'}
              </p>
              {searchTerm ? (
                <Button variant="outline" onClick={() => setSearchTerm('')}>
                  Clear Search
                </Button>
              ) : (
                <Button onClick={handleNewSession}>
                  Create New Session
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Rename dialog */}
      <Dialog open={isRenameDialogOpen} onOpenChange={setIsRenameDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rename Session</DialogTitle>
            <DialogDescription>
              Give this session a meaningful name for easier identification.
            </DialogDescription>
          </DialogHeader>
          
          <div className="py-4">
            <Label htmlFor="session-name" className="mb-2 block">
              Session Name
            </Label>
            <Input
              id="session-name"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Enter session name"
            />
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsRenameDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleRename}>
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default SessionsPage;
```

## C:\xampp\htdocs\DocTypeGen\public\src\pages\SettingsPage.tsx
```tsx
// src/pages/SettingsPage.tsx
import React, { useState } from 'react';
import { useAuth } from "@/contexts/AuthContext";
import { useTheme } from "@/contexts/ThemeContext";
import { Sun, Moon, Save, AlertCircle, Check, Key } from 'lucide-react';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import { Switch } from "@/components/ui/switch";

// Change password form schema
const passwordFormSchema = z.object({
  currentPassword: z.string().min(1, 'Current password is required'),
  newPassword: z.string().min(6, 'New password must be at least 6 characters'),
  confirmPassword: z.string().min(6, 'Please confirm your password'),
}).refine((data) => data.newPassword === data.confirmPassword, {
  message: "Passwords don't match",
  path: ['confirmPassword'],
});

type PasswordFormValues = z.infer<typeof passwordFormSchema>;

const SettingsPage: React.FC = () => {
  const { user } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [success, setSuccess] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // Profile settings
  const [profileData, setProfileData] = useState({
    email: 'user@example.com',
    displayName: user?.username || '',
  });
  
  // Password form
  const passwordForm = useForm<PasswordFormValues>({
    resolver: zodResolver(passwordFormSchema),
    defaultValues: {
      currentPassword: '',
      newPassword: '',
      confirmPassword: '',
    },
  });
  
  // Notification settings
  const [notifications, setNotifications] = useState({
    emailNotifications: true,
    smsNotifications: false,
    pushNotifications: true,
  });
  
  const handleProfileUpdate = () => {
    // In a real app, you would update the profile data via API
    setSuccess('Profile updated successfully');
    setTimeout(() => setSuccess(null), 3000);
  };
  
  const handlePasswordChange = (data: PasswordFormValues) => {
    // In a real app, you would change the password via API
    console.log('Password change data:', data);
    
    setSuccess('Password changed successfully');
    passwordForm.reset();
    setTimeout(() => setSuccess(null), 3000);
  };
  
  const handleNotificationChange = (key: keyof typeof notifications, value: boolean) => {
    setNotifications({
      ...notifications,
      [key]: value,
    });
    
    // In a real app, you would save notification settings via API
    setSuccess('Notification settings updated');
    setTimeout(() => setSuccess(null), 3000);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Settings</h1>
        <p className="text-muted-foreground mt-2">
          Manage your account settings and preferences
        </p>
      </div>
      
      {success && (
        <Alert variant="success">
          <Check className="h-4 w-4" />
          <AlertTitle>Success</AlertTitle>
          <AlertDescription>{success}</AlertDescription>
        </Alert>
      )}
      
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      
      <Tabs defaultValue="profile" className="space-y-4">
        <TabsList>
          <TabsTrigger value="profile">Profile</TabsTrigger>
          <TabsTrigger value="appearance">Appearance</TabsTrigger>
          <TabsTrigger value="password">Password</TabsTrigger>
          <TabsTrigger value="notifications">Notifications</TabsTrigger>
        </TabsList>
        
        <TabsContent value="profile" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Profile</CardTitle>
              <CardDescription>
                Manage your profile information
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="display-name">Display Name</Label>
                <Input
                  id="display-name"
                  value={profileData.displayName}
                  onChange={(e) => setProfileData({ ...profileData, displayName: e.target.value })}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={profileData.email}
                  onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                />
              </div>
            </CardContent>
            <CardFooter>
              <Button onClick={handleProfileUpdate}>
                <Save className="mr-2 h-4 w-4" />
                Save Changes
              </Button>
            </CardFooter>
          </Card>
        </TabsContent>
        
        <TabsContent value="appearance" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Appearance</CardTitle>
              <CardDescription>
                Customize the appearance of the application
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label>Theme</Label>
                  <p className="text-sm text-muted-foreground">
                    Switch between light and dark theme
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="icon"
                  onClick={toggleTheme}
                  aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} theme`}
                >
                  {theme === 'light' ? (
                    <Moon className="h-[1.2rem] w-[1.2rem]" />
                  ) : (
                    <Sun className="h-[1.2rem] w-[1.2rem]" />
                  )}
                </Button>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="password" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Change Password</CardTitle>
              <CardDescription>
                Update your password to keep your account secure
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Form {...passwordForm}>
                <form onSubmit={passwordForm.handleSubmit(handlePasswordChange)} className="space-y-4">
                  <FormField
                    control={passwordForm.control}
                    name="currentPassword"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Current Password</FormLabel>
                        <FormControl>
                          <Input type="password" placeholder="••••••••" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  
                  <FormField
                    control={passwordForm.control}
                    name="newPassword"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>New Password</FormLabel>
                        <FormControl>
                          <Input type="password" placeholder="••••••••" {...field} />
                        </FormControl>
                        <FormDescription>
                          Password must be at least 6 characters
                        </FormDescription>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  
                  <FormField
                    control={passwordForm.control}
                    name="confirmPassword"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Confirm Password</FormLabel>
                        <FormControl>
                          <Input type="password" placeholder="••••••••" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  
                  <Button type="submit" className="mt-2">
                    <Key className="mr-2 h-4 w-4" />
                    Change Password
                  </Button>
                </form>
              </Form>
            </CardContent>
          </Card>
        </TabsContent>
        
        <TabsContent value="notifications" className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Notifications</CardTitle>
              <CardDescription>
                Configure how you receive notifications
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="email-notifications">Email Notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    Receive notifications via email
                  </p>
                </div>
                <Switch
                  id="email-notifications"
                  checked={notifications.emailNotifications}
                  onCheckedChange={(checked) => handleNotificationChange('emailNotifications', checked)}
                />
              </div>
              
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="sms-notifications">SMS Notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    Receive notifications via SMS
                  </p>
                </div>
                <Switch
                  id="sms-notifications"
                  checked={notifications.smsNotifications}
                  onCheckedChange={(checked) => handleNotificationChange('smsNotifications', checked)}
                />
              </div>
              
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <Label htmlFor="push-notifications">Push Notifications</Label>
                  <p className="text-sm text-muted-foreground">
                    Receive push notifications in the browser
                  </p>
                </div>
                <Switch
                  id="push-notifications"
                  checked={notifications.pushNotifications}
                  onCheckedChange={(checked) => handleNotificationChange('pushNotifications', checked)}
                />
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default SettingsPage;
```

## C:\xampp\htdocs\DocTypeGen\public\src\pages\UsersPage.tsx
```tsx
// src/pages/UsersPage.tsx
import React, { useState, useEffect } from 'react';
import { Plus, Search, MoreHorizontal, Edit, Trash2, AlertCircle } from 'lucide-react';
import { useAuth } from "@/contexts/AuthContext";
import { userService } from "@/api/services";
import { User } from "@/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Spinner } from "@/components/ui/spinner";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useNavigate } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import * as z from 'zod';
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";

// Create user form schema
const createUserSchema = z.object({
  username: z.string().min(3, 'Username must be at least 3 characters'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  role: z.enum(['admin', 'user']),
});

type CreateUserFormValues = z.infer<typeof createUserSchema>;

// Edit user form schema (password is optional)
const editUserSchema = z.object({
  username: z.string().min(3, 'Username must be at least 3 characters'),
  password: z.string().min(6, 'Password must be at least 6 characters').optional().or(z.literal('')),
  role: z.enum(['admin', 'user']),
});

type EditUserFormValues = z.infer<typeof editUserSchema>;

const UsersPage: React.FC = () => {
  const { user: currentUser } = useAuth();
  const navigate = useNavigate();
  const [users, setUsers] = useState<User[]>([]);
  const [filteredUsers, setFilteredUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [isCreateDialogOpen, setIsCreateDialogOpen] = useState(false);
  const [isEditDialogOpen, setIsEditDialogOpen] = useState(false);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState(false);
  const [selectedUser, setSelectedUser] = useState<User | null>(null);
  
  // Create user form
  const createForm = useForm<CreateUserFormValues>({
    resolver: zodResolver(createUserSchema),
    defaultValues: {
      username: '',
      password: '',
      role: 'user',
    },
  });
  
  // Edit user form
  const editForm = useForm<EditUserFormValues>({
    resolver: zodResolver(editUserSchema),
    defaultValues: {
      username: '',
      password: '',
      role: 'user',
    },
  });
  
  // Redirect if not admin
  useEffect(() => {
    if (currentUser && currentUser.role !== 'admin') {
      navigate('/');
    }
  }, [currentUser, navigate]);
  
  // Fetch users on mount
  useEffect(() => {
    fetchUsers();
  }, []);
  
  // Filter users when search term changes
  useEffect(() => {
    if (searchTerm.trim() === '') {
      setFilteredUsers(users);
    } else {
      const term = searchTerm.toLowerCase();
      const filtered = users.filter(
        user => 
          user.username.toLowerCase().includes(term) ||
          user.role.toLowerCase().includes(term)
      );
      setFilteredUsers(filtered);
    }
  }, [searchTerm, users]);
  
  const fetchUsers = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await userService.getUsers();
      setUsers(response);
      setFilteredUsers(response);
    } catch (err) {
      console.error('Error fetching users:', err);
      setError('Failed to load users. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };
  
  const handleSearch = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
  };
  
  const openCreateDialog = () => {
    createForm.reset();
    setIsCreateDialogOpen(true);
  };
  
  const openEditDialog = (user: User) => {
    setSelectedUser(user);
    editForm.reset({
      username: user.username,
      password: '',
      role: user.role,
    });
    setIsEditDialogOpen(true);
  };
  
  const openDeleteDialog = (user: User) => {
    setSelectedUser(user);
    setIsDeleteDialogOpen(true);
  };
  
  const handleCreateUser = async (data: CreateUserFormValues) => {
    try {
      await userService.createUser(data.username, data.password, data.role);
      setIsCreateDialogOpen(false);
      await fetchUsers();
    } catch (err) {
      console.error('Error creating user:', err);
      setError('Failed to create user. Please try again.');
    }
  };
  
  const handleEditUser = async (data: EditUserFormValues) => {
    if (!selectedUser) return;
    
    try {
      await userService.updateUser(selectedUser.id, {
        username: data.username,
        role: data.role,
        ...(data.password ? { password: data.password } : {}),
      });
      setIsEditDialogOpen(false);
      await fetchUsers();
    } catch (err) {
      console.error('Error updating user:', err);
      setError('Failed to update user. Please try again.');
    }
  };
  
  const handleDeleteUser = async () => {
    if (!selectedUser) return;
    
    try {
      await userService.deleteUser(selectedUser.id);
      setIsDeleteDialogOpen(false);
      await fetchUsers();
    } catch (err) {
      console.error('Error deleting user:', err);
      setError('Failed to delete user. Please try again.');
    }
  };

  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-8rem)] items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">User Management</h1>
        <Button onClick={openCreateDialog}>
          <Plus className="mr-2 h-4 w-4" />
          Add User
        </Button>
      </div>
      
      {error && (
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Error</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
      
      <div className="flex items-center space-x-2">
        <Search className="h-4 w-4 text-muted-foreground" />
        <Input
          placeholder="Search users..."
          value={searchTerm}
          onChange={handleSearch}
          className="w-full md:w-[300px]"
        />
      </div>
      
      <Card>
        <CardHeader>
          <CardTitle>All Users</CardTitle>
          <CardDescription>
            Manage user accounts and permissions
          </CardDescription>
        </CardHeader>
        <CardContent>
          {filteredUsers.length > 0 ? (
            <div className="rounded-md border">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Username</TableHead>
                    <TableHead>Role</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredUsers.map((user) => (
                    <TableRow key={user.id}>
                      <TableCell className="font-medium">{user.username}</TableCell>
                      <TableCell>
                        <Badge variant={user.role === 'admin' ? "default" : "secondary"}>
                          {user.role}
                        </Badge>
                      </TableCell>
                      <TableCell className="text-right">
                        <DropdownMenu>
                          <DropdownMenuTrigger asChild>
                            <Button variant="ghost" size="sm">
                              <MoreHorizontal className="h-4 w-4" />
                              <span className="sr-only">Open menu</span>
                            </Button>
                          </DropdownMenuTrigger>
                          <DropdownMenuContent align="end">
                            <DropdownMenuLabel>Actions</DropdownMenuLabel>
                            <DropdownMenuSeparator />
                            <DropdownMenuItem onClick={() => openEditDialog(user)}>
                              <Edit className="mr-2 h-4 w-4" />
                              Edit
                            </DropdownMenuItem>
                            {user.id !== currentUser?.id && (
                              <DropdownMenuItem
                                className="text-destructive focus:text-destructive"
                                onClick={() => openDeleteDialog(user)}
                              >
                                <Trash2 className="mr-2 h-4 w-4" />
                                Delete
                              </DropdownMenuItem>
                            )}
                          </DropdownMenuContent>
                        </DropdownMenu>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-8 text-center">
              <h3 className="font-medium mb-1">No users found</h3>
              <p className="text-muted-foreground mb-4">
                {searchTerm ? 'No users match your search' : 'You have not created any users yet'}
              </p>
              {searchTerm ? (
                <Button variant="outline" onClick={() => setSearchTerm('')}>
                  Clear Search
                </Button>
              ) : (
                <Button onClick={openCreateDialog}>
                  Add New User
                </Button>
              )}
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Create User Dialog */}
      <Dialog open={isCreateDialogOpen} onOpenChange={setIsCreateDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New User</DialogTitle>
            <DialogDescription>
              Add a new user to the system. Users can be either administrators or regular users.
            </DialogDescription>
          </DialogHeader>
          
          <Form {...createForm}>
            <form onSubmit={createForm.handleSubmit(handleCreateUser)} className="space-y-4">
              <FormField
                control={createForm.control}
                name="username"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Username</FormLabel>
                    <FormControl>
                      <Input placeholder="Enter username" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <FormField
                control={createForm.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Password</FormLabel>
                    <FormControl>
                      <Input type="password" placeholder="Enter password" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <FormField
                control={createForm.control}
                name="role"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Role</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select a role" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="admin">Admin</SelectItem>
                        <SelectItem value="user">User</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormDescription>
                      Admins can manage users and access all features
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <DialogFooter>
                <Button type="submit">Create User</Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
      
      {/* Edit User Dialog */}
      <Dialog open={isEditDialogOpen} onOpenChange={setIsEditDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Edit User</DialogTitle>
            <DialogDescription>
              Update user details and permissions.
            </DialogDescription>
          </DialogHeader>
          
          <Form {...editForm}>
            <form onSubmit={editForm.handleSubmit(handleEditUser)} className="space-y-4">
              <FormField
                control={editForm.control}
                name="username"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Username</FormLabel>
                    <FormControl>
                      <Input placeholder="Enter username" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <FormField
                control={editForm.control}
                name="password"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Password</FormLabel>
                    <FormControl>
                      <Input type="password" placeholder="Enter new password (optional)" {...field} />
                    </FormControl>
                    <FormDescription>
                      Leave blank to keep the current password
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <FormField
                control={editForm.control}
                name="role"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Role</FormLabel>
                    <Select onValueChange={field.onChange} defaultValue={field.value}>
                      <FormControl>
                        <SelectTrigger>
                          <SelectValue placeholder="Select a role" />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        <SelectItem value="admin">Admin</SelectItem>
                        <SelectItem value="user">User</SelectItem>
                      </SelectContent>
                    </Select>
                    <FormDescription>
                      Admins can manage users and access all features
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
              
              <DialogFooter>
                <Button type="submit">Save Changes</Button>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
      
      {/* Delete User Confirmation Dialog */}
      <AlertDialog open={isDeleteDialogOpen} onOpenChange={setIsDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Are you sure?</AlertDialogTitle>
            <AlertDialogDescription>
              This will permanently delete the user{' '}
              <span className="font-medium">{selectedUser?.username}</span>.
              This action cannot be undone.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteUser}
              className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
            >
              Delete
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </div>
  );
};

export default UsersPage;
```

## C:\xampp\htdocs\DocTypeGen\public\src\pages\WorkflowPage.tsx
```tsx
// src/pages/WorkflowPage.tsx
import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams, Routes, Route } from 'react-router-dom';
import { CommandResponse, SessionStatus } from "@/types";
import { commandService } from "@/api/services";
import WorkflowStepper from "@/components/workflow/WorkflowStepper";
import FileUpload from "@/components/upload/FileUpload";
import ValidateStep from "@/components/workflow/ValidateStep";
import MappingStep from "@/components/workflow/MappingStep";
import HtmlGenerationStep from "@/components/workflow/HtmlGenerationStep";
import PdfGenerationStep from "@/components/workflow/PdfGenerationStep";
import LookupResolutionStep from "@/components/workflow/LookupResolutionStep";
import EntityCreationStep from "@/components/workflow/EntityCreationStep";
import SyncStep from "@/components/workflow/SyncStep";
import StorageStep from "@/components/workflow/StorageStep";
import { Spinner } from "@/components/ui/spinner";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { AlertCircle } from 'lucide-react';

const WorkflowPage: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const sessionHash = searchParams.get('session');
  
  const [activeStep, setActiveStep] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [sessionStatus, setSessionStatus] = useState<SessionStatus | null>(null);
  const [stepResults, setStepResults] = useState<Record<string, CommandResponse>>({});
  
  // Fetch session status on mount
  useEffect(() => {
    const fetchSessionStatus = async () => {
      setIsLoading(true);
      setError(null);
      
      try {
        const status = await commandService.getStatus();
        setSessionStatus(status);
        
        // Determine active step based on session status
        if (status.active_session) {
          // TODO: Determine active step based on last operation in session
          setActiveStep(1); // Default to validation step if session exists
        } else {
          setActiveStep(0); // Start with upload if no active session
          
          // Redirect to upload if no active session and no session hash in URL
          if (!sessionHash) {
            navigate('/app/workflow/upload');
          }
        }
      } catch (err) {
        console.error('Error fetching session status:', err);
        setError('Failed to load session status. Please try again.');
      } finally {
        setIsLoading(false);
      }
    };
    
    fetchSessionStatus();
  }, [sessionHash, navigate]);
  
  // Handle step completion
  const handleStepComplete = (step: number, result: CommandResponse) => {
    setStepResults({ ...stepResults, [step]: result });
    setActiveStep(step + 1);
  };
  
  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-8rem)] items-center justify-center">
        <Spinner size="lg" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive" className="max-w-3xl mx-auto">
        <AlertCircle className="h-4 w-4" />
        <AlertTitle>Error</AlertTitle>
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }
  
  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Document Processing Workflow</h1>
        <p className="text-muted-foreground mt-2">
          Follow the steps to process your data file into documents
        </p>
      </div>
      
      <WorkflowStepper activeStep={activeStep} />
      
      <Routes>
        <Route path="upload" element={<FileUpload />} />
        <Route path="" element={
          <>
            {activeStep === 1 && (
              <ValidateStep
                onComplete={(result) => handleStepComplete(1, result)}
              />
            )}
            
            {activeStep === 2 && (
              <MappingStep
                onComplete={(result) => handleStepComplete(2, result)}
                validationResult={stepResults[1]?.result}
              />
            )}
            
            {activeStep === 3 && (
              <HtmlGenerationStep
                onComplete={(result) => handleStepComplete(3, result)}
              />
            )}
            
            {activeStep === 4 && (
              <PdfGenerationStep
                onComplete={(result) => handleStepComplete(4, result)}
              />
            )}
            
            {activeStep === 5 && (
              <LookupResolutionStep
                onComplete={(result) => handleStepComplete(5, result)}
              />
            )}
            
            {activeStep === 6 && (
              <EntityCreationStep
                onComplete={(result) => handleStepComplete(6, result)}
              />
            )}
            
            {activeStep === 7 && (
              <SyncStep
                onComplete={(result) => handleStepComplete(7, result)}
              />
            )}
            
            {activeStep === 8 && (
              <StorageStep
                onComplete={(result) => handleStepComplete(8, result)}
              />
            )}
            
            {activeStep === 9 && (
              <div className="text-center py-12">
                <h2 className="text-2xl font-bold">Processing Complete!</h2>
                <p className="text-muted-foreground mt-2">
                  Your documents have been generated successfully.
                </p>
              </div>
            )}
          </>
        } />
      </Routes>
    </div>
  );
};

export default WorkflowPage;
```

## C:\xampp\htdocs\DocTypeGen\public\src\types\index.ts
```ts
// Add this at the top of your file
interface ImportMeta {
    readonly env: Record<string, any>;
}

/**
 * Central configuration for the Dashboard
 * Use this file to manage environment-specific settings
 */

// Export all lookup system types
export * from './lookup';

// User types
export interface User {
    id: number;
    username: string;
    role: 'admin' | 'user';
}


// Command types
export interface Command {
    func?: string;
    args?: string[];
    description: string;
}



export interface FieldMatch {
    field: string;
    column: string | null;
    match_type: string;
    score: number;
    validation: {
        valid: boolean;
        valid_count: number;
        total_count: number;
        valid_percentage: number;
        errors: string[];
    };
}

export interface RowValidation {
    row_id: number;
    valid: boolean;
    fields: Array<{
        field: string;
        column: string | null;
        value: string;
        expected?: string;
        status: 'MATCH' | 'MISMATCH' | 'MISSING_COLUMN';
        valid: boolean;
        errors: string[];
    }>;
}

export interface SchemaField {
    slug: string[];
    validate_type: string;
    required: boolean;
    description?: string;
    regex?: string;
    list?: string;
    distance?: number;
    enum?: string;
}

// HTML generation types
export interface HtmlGenerationResult {
    num_files: number;
    template_name: string;
    output_dir: string;
    html_files: string[];
    errors: Array<{
        row: number;
        error: string;
    }>;
    log_file: string;
}

// Log types
export interface LogDirectory {
    hash: string;
    name: string;
    date: string;
    file_count: number;
}

export interface LogInfo {
    hash: string;
    name: string;
    date: string;
    html_files: string[];
    pdf_files: string[];
    log_files: string[];
}

// Form data for file upload
export interface FileUploadForm {
    file: File | null;
}










// User types
export interface User {
    id: number;
    username: string;
    role: 'admin' | 'user';
}

export interface AuthResponse {
    user: User;
    token: string;
}

// Session & Log types
export interface Session {
    hash: string;
    name: string | null;
    date: string;
    document_type?: string;
    file_count: number;
    last_operation?: string;
}

export interface LogDirectory {
    hash: string;
    name: string;
    date: string;
    document_type?: string;
    file_count: number;
    last_operation?: string;
}

export interface LogInfo {
    hash: string;
    name: string;
    date: string;
    document_type?: string;
    html_files: string[];
    pdf_files: string[];
    log_files: string[];
}

export interface SessionStatus {
    active_session: boolean;
    session_hash: string;
    document_type?: string;
    last_operation?: string;
}

// Command responses
export interface CommandResponse {
    success: boolean;
    command: string;
    result: any;
    error?: string;
}

// Validation types
export interface ValidationFieldMatch {
    field: string;
    column: string | null;
    status: 'matched' | 'missing';
    required: boolean;
    data_type: string;
}

export interface ValidationResult {
    valid: boolean;
    errors: string[];
    field_matches: Record<string, ValidationFieldMatch>;
    required_missing: string[];
    document_type: string;
    match_score: number;
    schema_id: string;
    valid_rows: number;
    invalid_rows: number;
    total_rows: number;
    success_rate: number;
}


export interface MappingResult {
    schema_fields: Record<string, SchemaField>;
    mapped_fields: Record<string, string>;
    missing_required?: string[];
    validation_issues?: string[];
}

// HTML generation types
export interface HtmlGenerationError {
    row: number;
    error: string;
}


// PDF generation types
export interface PdfGenerationError {
    file: string;
    error: string;
}

export interface PdfGenerationResult {
    num_files: number;
    pdf_files: string[];
    total_time: number;
    errors: PdfGenerationError[];
    log_file: string;
}

// Config
export interface AppConfig {
    api: {
        baseUrl: string;
    };
    auth: {
        useJwtAuth: boolean;
        apiKey?: string;
        tokenStorageKey: string;
        userStorageKey: string;
    };
    upload: {
        maxFileSize: number;
        acceptedFileTypes: string;
    };
}

export interface ImportResult {
    hash: string;
    file: string;
    document_type: string;
    status: string;
}
```

## C:\xampp\htdocs\DocTypeGen\public\src\types\lookup.ts
```ts
// src/types/lookup.ts
// Lookup system type definitions

export interface LookupAttempt {
  id: number;
  document_id: number;
  lookup_type: string;
  lookup_field: string;
  lookup_value: string;
  lookup_match?: string | null;
  status: 'pending' | 'matched' | 'exception';
  created_at: string;
  updated_at?: string;
}

export interface LookupException {
  id: number;
  document_id: number;
  input_file: string;
  row: number;
  data: Record<string, any>;
  lookup_type: string;
  lookup_field: string;
  lookup_value: string;
  exception_message: string;
  potential_matches?: Array<{
    id: string | number;
    display: string;
    score?: number;
  }>;
  status: 'pending' | 'accepted' | 'rejected' | 'for_creation';
  resolution_value?: string | null;
  created_at: string;
  updated_at?: string;
}

export interface LookupExceptionsList {
  exceptions: LookupException[];
  total: number;
  pending: number;
  resolved: number;
  for_creation: number;
}

export interface LookupResolutionResult {
  status: 'success' | 'error';
  message: string;
  records_processed: number;
  successful_lookups: number;
  exceptions: number;
  for_creation: number;
  execution_time: number;
}

export interface ExceptionResolutionRequest {
  accept: boolean;
  lookup_value?: string;
  mark_for_creation?: boolean;
  apply_to_similar?: boolean;
  similarity_criteria?: {
    lookup_type?: boolean;
    lookup_field?: boolean;
    exception_message?: boolean;
  };
}

export interface ExceptionResolutionResult {
  status: 'success' | 'error';
  message: string;
  affected_count: number;
  updated_exceptions?: LookupException[];
}

export interface Entity {
  id?: number;
  entity_type: string;
  name: string;
  properties: Record<string, any>;
  created_from_exception?: number;
  created_at?: string;
  updated_at?: string;
}

export interface EntityCreationResult {
  status: 'success' | 'error';
  message: string;
  entity?: Entity;
  affected_exceptions?: number;
}

export interface EntitiesForCreationResult {
  entities: Array<{
    entity_type: string;
    lookup_field: string;
    lookup_value: string;
    exception_count: number;
    sample_data: Record<string, any>;
    exceptions: number[];
  }>;
  total: number;
}

```

## C:\xampp\htdocs\DocTypeGen\public\src\utils\mappingUtils.ts
```ts
/**
 * Mapping Utilities
 * Contains functions for handling field-to-column and column-to-type mappings
 */

import { MappingStructure } from './validationTypes';

/**
 * Prepare mapping update data based on changes between original and current mapping
 */
export function prepareMappingUpdates(
  currentMapping: MappingStructure,
  originalMapping: MappingStructure
): Record<string, string> {
  const updateData: Record<string, string> = {};
  
  // Check for removed mappings or changed mappings
  for (const [originalColumn, originalType] of Object.entries(originalMapping)) {
    const typeName = originalType.type;
    
    // Check if this mapping was removed
    if (!currentMapping[originalColumn]) {
      // This column mapping was removed
      updateData[`column:${typeName}`] = ""; // empty string means remove mapping
    }
    // Check if the type was changed
    else if (currentMapping[originalColumn].type !== typeName) {
      // This column was mapped to a different type
      updateData[`column:${typeName}`] = ""; // Remove old mapping
      updateData[`column:${currentMapping[originalColumn].type}`] = originalColumn; // Add new mapping
    }
  }
  
  // Check for new mappings
  for (const [column, typeInfo] of Object.entries(currentMapping)) {
    const originalTypeInfo = originalMapping[column];
    if (!originalTypeInfo) {
      // This is a new mapping
      updateData[`column:${typeInfo.type}`] = column;
    }
  }
  
  return updateData;
}

/**
 * Update mapping with a new field-to-column mapping
 */
export function updateFieldMapping(
  currentMapping: MappingStructure,
  typeName: string,
  columnName: string
): MappingStructure {
  const updatedMapping = { ...currentMapping };
  
  // First, check if this column is already mapped to a different type
  for (const [existingColumn, typeInfo] of Object.entries(updatedMapping)) {
    if (existingColumn === columnName && typeInfo.type !== typeName) {
      // Remove this mapping
      delete updatedMapping[existingColumn];
      break;
    }
  }
  
  // Find and remove any existing mapping for this type
  for (const [column, typeInfo] of Object.entries(updatedMapping)) {
    if (typeInfo.type === typeName) {
      delete updatedMapping[column];
      break;
    }
  }
  
  // Then add the new mapping
  if (columnName) {
    updatedMapping[columnName] = { type: typeName };
  }
  
  return updatedMapping;
}

```

## C:\xampp\htdocs\DocTypeGen\public\src\utils\validationHelpers.ts
```ts
/**
 * Validation Helpers
 * Contains utility functions for working with validation data
 */

import { SchemaFieldInfo, SchemaValidationType } from './validationTypes';

/**
 * Get detailed field information for validation tooltips
 */
export function getFieldValidationInfo(
  fieldName: string, 
  validationTypes?: Record<string, SchemaValidationType>
): string {
  if (!validationTypes || !validationTypes[fieldName]) return "";
  
  const fieldInfo = validationTypes[fieldName];
  const details = fieldInfo.fieldDetails;
  
  let infoText = fieldInfo.description || "";
  
  if (details.required) {
    infoText += "\n• Required field";
  }
  
  if (details.validate_type === "REGEX" && details.regex) {
    infoText += `\n• Pattern: ${details.regex}`;
  } else if (details.validate_type === "LEV_DISTANCE") {
    infoText += `\n• Matched against the ${details.list} list`;
    infoText += `\n• Minimum match score: ${details.distance}%`;
  } else if (details.validate_type === "ENUM" && details.enum) {
    infoText += `\n• Must be one of the values in ${details.enum}`;
  }
  
  return infoText;
}

/**
 * Process schema information to extract validation types and field details
 */
export function processSchemaInfo(schema: any): {
  schemaFields: SchemaFieldInfo[];
  validationTypes: Record<string, SchemaValidationType>;
  allValidationTypes: Record<string, { description: string, details: any }>;
  passThreshold: number;
} {
  // Default values
  const schemaFields: SchemaFieldInfo[] = [];
  const validationTypes: Record<string, SchemaValidationType> = {};
  const allValidationTypes: Record<string, { description: string, details: any }> = {};
  let passThreshold = 80;

  if (!schema) {
    return { schemaFields, validationTypes, allValidationTypes, passThreshold };
  }

  // Extract pass threshold from schema
  if (schema.pass_threshold) {
    passThreshold = schema.pass_threshold;
  }
  
  // Extract schema fields and validation types
  if (schema.schema) {
    Object.entries(schema.schema).forEach(([fieldName, fieldConfig]: [string, any]) => {
      const validateType = fieldConfig.validate_type || "NONE";
      const description = fieldConfig.description || `${validateType} validation`;
      
      // Add to schema fields list
      schemaFields.push({
        fieldName,
        description,
        validateType,
        required: !!fieldConfig.required,
        details: fieldConfig
      });
      
      // Add to validation types map
      validationTypes[fieldName] = {
        type: validateType,
        description,
        fieldDetails: fieldConfig
      };
      
      // Add to unique validation types
      if (!allValidationTypes[validateType]) {
        allValidationTypes[validateType] = {
          description,
          details: fieldConfig
        };
      }
    });
  }

  return {
    schemaFields,
    validationTypes,
    allValidationTypes,
    passThreshold
  };
}

/**
 * Extract column names from validation row data
 */
export function extractAvailableColumns(rowValidations: any[]): string[] {
  if (!rowValidations || rowValidations.length === 0) {
    return [];
  }

  const firstRow = rowValidations[0];
  
  // Try to get columns from fields array (new structure)
  if (firstRow.fields) {
    return firstRow.fields
      .filter((field: any) => field.column)
      .map((field: any) => field.column);
  }
  
  // Try to get columns from validations object (old structure)
  if (firstRow.validations) {
    return Object.keys(firstRow.validations);
  }
  
  return [];
}

```

## C:\xampp\htdocs\DocTypeGen\public\src\utils\validationTypes.ts
```ts
/**
 * Validation Types and Type Utilities
 * Contains type definitions and utility functions for validation
 */

/**
 * Schema field information
 */
export interface SchemaFieldInfo {
  fieldName: string;
  description: string;
  validateType: string;
  required: boolean;
  details: Record<string, any>;
}

/**
 * Schema validation type information
 */
export interface SchemaValidationType {
  type: string;
  description: string;
  fieldDetails: Record<string, any>;
}

/**
 * Validation row data structure
 */
export interface ValidationRowData {
  row_id: number;
  valid: boolean;
  fields?: {
    field: string;
    valid: boolean;
    column?: string;
    value?: string;
    expected?: string;
    status?: string;
    errors?: string[];
  }[];
  validations?: Record<string, {
    valid: boolean;
    error?: string;
    value?: string;
  }>;
}

/**
 * Extended validation result with full row data
 */
export interface ExtendedValidationResult {
  document_type?: string;
  match_score?: number;
  total_rows?: number;
  valid_rows?: number;
  invalid_rows?: number;
  success_rate?: number;
  row_validations?: ValidationRowData[];
}

/**
 * Validation field match structure
 */
export interface ValidationFieldMatch {
  field: string;
  column: string;
  status: string;
  required: boolean;
  data_type: string;
}

/**
 * Column to Type mapping structure
 */
export interface MappingItem {
  type: string;
  validation?: string;
}

/**
 * Full mapping structure definition
 */
export type MappingStructure = Record<string, MappingItem>;

/**
 * Get validation type badge color based on validation type
 */
export function getValidationTypeColor(type: string): string {
  switch (type) {
    case 'REGEX': return 'bg-blue-500';
    case 'LEV_DISTANCE': return 'bg-purple-500';
    case 'SA_ID_NUMBER': return 'bg-green-500';
    case 'BANK_ACCOUNT_NUMBER': return 'bg-yellow-500';
    case 'DECIMAL_AMOUNT': return 'bg-red-500';
    case 'UNIX_DATE': return 'bg-indigo-500';
    case 'ENUM': return 'bg-orange-500';
    default: return 'bg-gray-500';
  }
}

```

## C:\xampp\htdocs\DocTypeGen\public\vite-env.d.ts
```ts
/// <reference types="vite/client" />

interface ImportMeta {
    readonly env: Record<string, any>;
}
```

## C:\xampp\htdocs\DocTypeGen\public\vite.config.d.ts
```ts
declare const _default: import("vite").UserConfig;
export default _default;

```

## C:\xampp\htdocs\DocTypeGen\public\vite.config.ts
```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      '@components': path.resolve(__dirname, './src/components'),
      '@ui': path.resolve(__dirname, './src/components/ui'),
      '@lib': path.resolve(__dirname, './src/lib'),
      '@contexts': path.resolve(__dirname, './src/contexts'),
      '@api': path.resolve(__dirname, './src/api'),
      '@types': path.resolve(__dirname, './src/types'),
      '@pages': path.resolve(__dirname, './src/pages')
    }
  },
  build: {
    outDir: './build',
    emptyOutDir: true
  }
})
```

