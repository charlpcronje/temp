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
