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
