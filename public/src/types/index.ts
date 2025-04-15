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
    type: string;
    validation?: string;
    validation_type?: string;
    slug: string[];
    validate_type?: string;
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