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
    const response = await apiClient.get<any[]>('/api/logs');

    // Convert the backend response to the expected LogDirectory format
    return response.data.map((item: any) => ({
      hash: item.hash,
      name: item.name || null,
      date: item.timestamp || new Date().toISOString(),
      document_type: item.metadata?.document_type || undefined,
      file_count: item.file_count || 0,
      last_operation: item.status === 'active' ? 'ACTIVE' : undefined
    }));
  },

  getLogInfo: async (hash: string): Promise<LogInfo> => {
    const response = await apiClient.get<any>(`/api/logs/${hash}`);

    // Convert the backend response to the expected LogInfo format
    const data = response.data;

    // Extract HTML, PDF, and log files from the files array
    const html_files: string[] = [];
    const pdf_files: string[] = [];
    const log_files: string[] = [];

    if (data.files && Array.isArray(data.files)) {
      data.files.forEach((file: any) => {
        const path = file.path.toLowerCase();
        if (path.endsWith('.html')) {
          html_files.push(file.name);
        } else if (path.endsWith('.pdf')) {
          pdf_files.push(file.name);
        } else if (path.endsWith('.log') || path.endsWith('.json')) {
          log_files.push(file.name);
        }
      });
    }

    return {
      hash: data.hash,
      name: data.name || null,
      date: data.timestamp || new Date().toISOString(),
      document_type: data.metadata?.document_type || undefined,
      html_files,
      pdf_files,
      log_files
    };
  },

  renameLog: async (hash: string, name: string): Promise<void> => {
    await apiClient.post(`/api/logs/${hash}/rename`, { name });
  },

  activateSession: async (hash: string): Promise<CommandResponse> => {
    const response = await apiClient.post<CommandResponse>(`/api/sessions/${hash}/activate`);
    return response.data;
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