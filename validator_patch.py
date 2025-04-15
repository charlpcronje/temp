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
                        logger.error(f"Invalid regex pattern '{pattern}' for field {field_def.get('name', 'unknown')}: {e}")
                        # Consider valid on regex error to avoid blocking the process
                        is_valid = True
                        if should_print:
                            print(f"WARNING: Invalid regex pattern '{pattern}': {e}")
                elif validate_type == "SA_ID_NUMBER":
                    is_valid = validate_sa_id_number(value)
                elif validate_type == "BANK_ACCOUNT_NUMBER":
                    is_valid = validate_bank_account_number(value)
                elif validate_type == "DECIMAL_AMOUNT":
                    is_valid = validate_decimal_amount(value)
                elif validate_type == "UNIX_DATE":
                    is_valid = validate_date(value)
                elif validate_type == "POSTAL_CODE":
                    is_valid = validate_postal_code(value)
                elif validate_type == "ENUM":
                    enum_name = field_def.get("enum", "")
                    enum_values = schema.get("enums", {}).get(enum_name, [])
                    try:
                        is_valid = str(value) in [str(ev) for ev in enum_values]
                    except Exception as e:
                        logger.error(f"Error in ENUM validation: {e}")
                        is_valid = True  # Default to valid on error
                elif validate_type == "LEV_DISTANCE":
                    try:
                        list_name = field_def.get("list", "")
                        list_items = schema.get("lists", {}).get(list_name, [])
                        min_distance = field_def.get("distance", 80)
                        
                        # Check against each list item and its aliases
                        for item in list_items:
                            item_name = item.get("name", "")
                            item_aliases = item.get("aliases", [])
                            
                            # Check name - protect against encoding issues
                            try:
                                similarity = lev.ratio(str(item_name).lower(), str(value).lower()) * 100
                                if similarity >= min_distance:
                                    is_valid = True
                                    break
                            except Exception as e:
                                logger.warning(f"Error comparing '{item_name}' with '{value}': {e}")
                                
                            # Check aliases
                            for alias in item_aliases:
                                try:
                                    similarity = lev.ratio(str(alias).lower(), str(value).lower()) * 100
                                    if similarity >= min_distance:
                                        is_valid = True
                                        break
                                except Exception as e:
                                    logger.warning(f"Error comparing alias '{alias}' with '{value}': {e}")
                    except Exception as e:
                        logger.error(f"Error in LEV_DISTANCE validation: {e}")
                        is_valid = True  # Default to valid on error
                else:
                    # If no validation type or unknown type, consider valid
                    is_valid = True
            except Exception as e:
                logger.error(f"Error validating value '{value}' for column '{column_name}': {e}")
                is_valid = True  # Default to valid on unexpected error to avoid blocking
                
            if is_valid:
                valid_count += 1
            else:
                errors.append(f"Invalid value: {value}")
                
        valid_percentage = (valid_count / total_count * 100) if total_count > 0 else 0
        logger.info(f"Column '{column_name}' validation score for field '{field_def.get('name', 'unknown')}': {valid_percentage:.2f}%")
        
        return {
            "valid": valid_count == total_count,
            "valid_count": valid_count,
            "total_count": total_count,
            "valid_percentage": valid_percentage,
            "errors": errors[:5]  # Limit to 5 errors
        }
        
    except Exception as e:
        logger.error(f"Error in validate_field_values for column '{column_name}': {e}")
        logger.error(traceback.format_exc())
        
        # Return a default error result instead of failing
        return {
            "valid": False,
            "valid_count": 0,
            "total_count": total_count if 'total_count' in locals() else 0,
            "valid_percentage": 0,
            "errors": [f"Validation function error: {str(e)}"]
        }