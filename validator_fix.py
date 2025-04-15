# validator_fix.py
"""
Fixed implementation of validator functions with proper error handling.
"""

import os
import json
import re
import logging
from datetime import datetime
from typing import Dict, List, Any, Tuple, Optional, Set, Union
import traceback

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ValidatorError(Exception):
    """Base exception for validation errors."""
    pass


class Validator:
    """Handles validation of data against schema definitions."""
    
    def __init__(self):
        self.schemas_dir = "schemas"
        self._schema_cache = {}
        
    def load_schemas(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all schema definitions from the schemas directory.
        Uses caching to avoid repeated disk reads.
        
        Returns:
            Dict mapping schema names to schema objects
        """
        logger.info(f"Loading schemas from directory: {self.schemas_dir}")
        
        # Return cached schemas if available
        if self._schema_cache:
            logger.info(f"Using cached schemas: {list(self._schema_cache.keys())}")
            return self._schema_cache
            
        schemas = {}
        
        try:
            if not os.path.isdir(self.schemas_dir):
                logger.warning(f"Schemas directory not found: {self.schemas_dir}")
                return schemas
                
            # Get list of schema files
            try:
                schema_files = [f for f in os.listdir(self.schemas_dir) if f.endswith(".json")]
            except OSError as e:
                logger.error(f"Error listing schemas directory: {e}")
                return schemas
                
            if not schema_files:
                logger.warning(f"No schema files found in {self.schemas_dir}")
                return schemas
                
            # Load each schema file
            for filename in schema_files:
                schema_path = os.path.join(self.schemas_dir, filename)
                schema_name = os.path.splitext(filename)[0]
                
                try:
                    with open(schema_path, 'r') as f:
                        schema = json.load(f)
                        
                    # Validate schema structure
                    if "schema" not in schema:
                        logger.warning(f"Invalid schema format in {schema_path}: 'schema' key not found")
                        continue
                        
                    schemas[schema_name] = schema
                    logger.info(f"Loaded schema: {schema_name} (type: {schema.get('type', 'unknown')})")
                    logger.info(f"Schema has {len(schema['schema'])} field definitions")
                    
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing schema {schema_path}: {e}")
                except OSError as e:
                    logger.error(f"Error reading schema file {schema_path}: {e}")
                except Exception as e:
                    logger.error(f"Unexpected error loading schema {schema_path}: {e}")
                    
            # Cache for future use
            self._schema_cache = schemas
        except Exception as e:
            logger.error(f"Unexpected error in load_schemas: {e}")
            
        return schemas
        
    def validate_field_values(self, column_name: str, field_def: Dict[str, Any],
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
            logger.info(f"Validating column '{column_name}' against field definition: {field_def.get('name', 'unknown')}")
            validate_type = field_def.get("validate_type", "NONE")
            logger.info(f"Validation type: {validate_type}")
            
            # Get values with proper handling for missing column
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
            invalid_samples = []
            
            logger.info(f"Found {total_count} values to validate")
            
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
                error_message = None
                
                try:
                    # Skip empty values that aren't required
                    if not value and not field_def.get("required", False):
                        is_valid = True
                    elif validate_type == "REGEX":
                        pattern = field_def.get("regex", ".*")
                        try:
                            is_valid = bool(re.match(pattern, str(value)))
                        except re.error as e:
                            logger.error(f"Invalid regex pattern '{pattern}': {e}")
                            error_message = f"Invalid regex pattern: {e}"
                            is_valid = False
                    elif validate_type == "SA_ID_NUMBER":
                        is_valid = self.validate_sa_id_number(value)
                    elif validate_type == "BANK_ACCOUNT_NUMBER":
                        is_valid = self.validate_bank_account_number(value)
                    elif validate_type == "DECIMAL_AMOUNT":
                        is_valid = self.validate_decimal_amount(value)
                    elif validate_type == "UNIX_DATE":
                        is_valid = self.validate_date(value)
                    elif validate_type == "POSTAL_CODE":
                        is_valid = self.validate_postal_code(value)
                    elif validate_type == "ENUM":
                        enum_name = field_def.get("enum", "")
                        enum_values = schema.get("enums", {}).get(enum_name, [])
                        is_valid = str(value) in [str(ev) for ev in enum_values]
                    else:
                        # If no validation type or unknown type, consider valid
                        is_valid = True
                except Exception as e:
                    logger.error(f"Error validating value '{value}' for column '{column_name}': {e}")
                    error_message = f"Validation error: {str(e)}"
                    is_valid = False
                    
                if is_valid:
                    valid_count += 1
                else:
                    error = error_message or f"Invalid value: {value}"
                    errors.append(error)
                    if len(invalid_samples) < 5:  # Limit samples
                        invalid_samples.append(value)
                        
            valid_percentage = (valid_count / total_count * 100) if total_count > 0 else 0
            
            logger.info(f"Column '{column_name}' validation score for field '{field_def.get('name', 'unknown')}': {valid_percentage:.2f}%")
            
            return {
                "valid": valid_count == total_count,
                "valid_count": valid_count,
                "total_count": total_count,
                "valid_percentage": valid_percentage,
                "errors": errors[:5],  # Limit to 5 errors
                "invalid_samples": invalid_samples
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
                "errors": [f"Validation function error: {str(e)}"],
                "invalid_samples": []
            }
            
    def validate_sa_id_number(self, value: Any) -> bool:
        """Validate South African ID number."""
        try:
            # Convert to string and remove any spaces or hyphens
            value = re.sub(r'[\s\-]', '', str(value))
            
            # Basic format check: 13 digits
            if not re.match(r'^\d{13}$', value):
                return False
                
            # TODO: Implement full SA ID validation logic if needed
            # For now, just check the basic format
            
            return True
        except Exception as e:
            logger.warning(f"SA ID validation error: {e}")
            return False
            
    def validate_bank_account_number(self, value: Any) -> bool:
        """Validate bank account number."""
        try:
            # Convert to string and remove any spaces, hyphens, or commas
            value = re.sub(r'[\s\-,]', '', str(value))
            
            # Most SA bank accounts are 10-12 digits
            # Some may include special characters like *
            # Allow basic formats for now
            if re.match(r'^[0-9\*]{6,12}$', value):
                return True
                
            return False
        except Exception as e:
            logger.warning(f"Bank account validation error: {e}")
            return False
            
    def validate_decimal_amount(self, value: Any) -> bool:
        """Validate decimal amount."""
        try:
            # Convert to string and remove currency symbols, spaces, and commas
            value = re.sub(r'[$£€\s,]', '', str(value))
            
            # Check if it's a valid decimal number
            float(value)
            return True
        except (ValueError, TypeError):
            return False
        except Exception as e:
            logger.warning(f"Decimal amount validation error: {e}")
            return False
            
    def validate_date(self, value: Any) -> bool:
        """Validate date in various formats."""
        try:
            value = str(value)
            
            # Try common date formats
            date_formats = [
                '%Y-%m-%d', '%d/%m/%Y', '%m/%d/%Y', '%d-%m-%Y', '%m-%d-%Y',
                '%d.%m.%Y', '%m.%d.%Y', '%Y/%m/%d', '%d %b %Y', '%d %B %Y'
            ]
            
            for fmt in date_formats:
                try:
                    datetime.strptime(value, fmt)
                    return True
                except ValueError:
                    continue
                    
            # Try Unix timestamp
            try:
                ts = float(value)
                datetime.fromtimestamp(ts)
                return True
            except (ValueError, TypeError, OverflowError):
                pass
                
            return False
        except Exception as e:
            logger.warning(f"Date validation error: {e}")
            return False
            
    def validate_postal_code(self, value: Any) -> bool:
        """Validate postal/zip code."""
        try:
            # Convert to string and remove spaces
            value = re.sub(r'\s', '', str(value))
            
            # Different countries have different formats
            # Allow digits, possibly with a hyphen for now
            if re.match(r'^[0-9\-]{4,10}$', value):
                return True
                
            return False
        except Exception as e:
            logger.warning(f"Postal code validation error: {e}")
            return False


# Usage example
if __name__ == "__main__":
    validator = Validator()
    schemas = validator.load_schemas()
    print(f"Loaded {len(schemas)} schemas")