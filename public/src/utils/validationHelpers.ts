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
