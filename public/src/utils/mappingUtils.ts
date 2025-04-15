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
