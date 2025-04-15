# validator_patch.py
"""
Patch for the validator module to fix the error with regex validation.

Apply this patch by replacing the validate_field_values function in the core/validator.py file.
"""

import re
import logging
import traceback
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

def validate_field_values(column_name: str, field_def: Dict[str, Any],
                         data: List[Dict[str, Any]],
                         schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate the values in a column against the field definition.
    
    Args:
        column_name: Name of the column to validate
        field_def: Field definition from schema
        data: Imported data rows
        schema: Full schema object
        
    Returns:
        Dict with validation results
    """
    try:
        print(f"Validating column '{column_name}' against field definition: {field_def.get('name', 'unknown')}")
        validate_type = field_def.get("validate_type", "NONE")
        print(f"Validation type: {validate_type}")
        
        # Get values with proper error handling
        values = []
        for row in data:
            try:
                values.append(row.get(column_name, ""))
            except Exception as e:
                logger.warning(f"Error getting value for column '{column_name}': {e}")
                values.append("")
                
        total_count = len(values)
        valid_count = 0
        errors = []
        print(f"Found {total_count} values to validate")
        
        # Skip empty values if field is not required
        if not field_def.get("required", False):
            non_empty_values = []
            for v in values:
                if v:
                    non_empty_values.append(v)
            if non_empty_values:
                values = non_empty_values
                total_count = len(values)
            
        # Validate based on type
        for i, value in enumerate(values):
            is_valid = False
            
            # Only print the first 5 validations to avoid flooding the console
            should_print = i < 5
            
            try:
                if not value and not field_def.get("required", False):
                    is_valid = True
                    if should_print:
                        print(f"Value '{value}' is empty and field is not required, so it's valid")
                elif validate_type == "REGEX":
                    pattern = field_def.get("regex", ".*")
                    try:
                        is_valid = bool(re.match(pattern, str(value)))
                        if should_print:
                            if is_valid:
                                print(f"Value '{value}' matches regex pattern '{pattern}'")
                            else:
                                print(f"Value '{value}' does NOT match regex pattern '{pattern}'")
                    except re.error as e: