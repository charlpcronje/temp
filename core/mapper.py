#!/usr/bin/env python
# core\mapper.py
"""
Field Mapper - Generate and manage field mapping files.
"""

import os
import json
import logging
from typing import Dict, List, Any, Optional
import shutil

from core.session import get_current_session, get_session_dir, update_session_status
from core.importer import get_table_data
from core.validator import validate_data, load_schemas
from core.logger import HTMLLogger

# Configure logging
logger = logging.getLogger(__name__)


def create_mapping_entry(field_name: str, field_def: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a comprehensive mapping entry with all schema field properties.

    Args:
        field_name: Name of the field
        field_def: Field definition from schema

    Returns:
        Dict containing all mapping properties
    """
    validate_type = field_def.get("validate_type", "NONE")

    # Create a comprehensive mapping with all schema field properties
    mapping_entry = {
        "type": field_name,
        "validation": validate_type,
        "validation_type": validate_type  # For compatibility with example format
    }

    # Copy all other properties from the field definition
    if field_def.get("required"):
        mapping_entry["required"] = field_def["required"]

    if field_def.get("description"):
        mapping_entry["description"] = field_def["description"]

    if field_def.get("regex"):
        mapping_entry["regex"] = field_def["regex"]

    if field_def.get("list"):
        mapping_entry["list"] = field_def["list"]

    if field_def.get("distance"):
        mapping_entry["distance"] = field_def["distance"]

    if field_def.get("enum"):
        mapping_entry["enum"] = field_def["enum"]

    # Add slug if available or create one with the field name
    mapping_entry["slug"] = field_def.get("slug", [field_name])

    return mapping_entry


def generate_mapping_file() -> Dict[str, Any]:
    """
    Generate a field mapping file based on validation results.
    If a mapping file already exists, it will be loaded instead of generating a new one.
    Ensures document type detection is performed if not already set.
    """
    # Get current session
    session_hash = get_current_session()
    if not session_hash:
        raise ValueError("No active session found")

    # --- ENFORCE DOCUMENT TYPE DETECTION ---
    from core.session import update_session_status
    import copy
    import datetime
    status_path = os.path.join(os.getcwd(), 'status.json')
    # Load status.json
    try:
        with open(status_path, 'r', encoding='utf-8') as f:
            status_data = json.load(f)
    except Exception as e:
        logger.error(f"Could not load status.json: {e}")
        raise
    doc_type = status_data.get('current_state', {}).get('document_type', '')
    if not doc_type:
        # Perform schema detection
        logger.info("No document_type set, running schema detection...")
        schemas = load_schemas()
        # Get table data for scoring
        try:
            table_name, all_columns, data_rows = get_table_data(session_hash)
        except Exception as e:
            logger.error(f"Failed to get table data for schema detection: {e}")
            raise
        best_score = -1
        best_schema = None
        best_matches = None
        for schema_name, schema in schemas.items():
            try:
                from core.validator import match_schema
                score, matches = match_schema(schema, all_columns, data_rows)
                logger.info(f"Schema {schema_name} match score: {score:.2f}%")
                if score > best_score:
                    best_score = score
                    best_schema = schema_name
                    best_matches = matches
            except Exception as e:
                logger.warning(f"Error matching schema {schema_name}: {e}")
                continue
        if best_schema is None or best_score < 1.0:
            logger.error("No suitable schema could be detected for the uploaded data.")
            raise ValueError("No suitable document type could be detected from the data.")
        # Set document_type in status.json
        logger.info(f"Detected document_type: {best_schema} (score: {best_score:.2f}%)")
        status_data['current_state']['document_type'] = best_schema
        status_data['last_updated'] = datetime.datetime.utcnow().isoformat()
        with open(status_path, 'w', encoding='utf-8') as f:
            json.dump(status_data, f, indent=2)
        # Also update in-memory doc_type
        doc_type = best_schema
        # Optionally: call update_session_status if needed
        update_session_status(session_hash, operation="DETECT_DOCUMENT_TYPE")

    # Continue with mapping generation as before

    """
    Generate a field mapping file based on validation results.
    If a mapping file already exists, it will be loaded instead of generating a new one.

    Returns:
        Dict containing mapping information

    Raises:
        ValueError: If no active session or validation results
        OSError: If mapping file cannot be written
    """
    # Get current session
    session_hash = get_current_session()
    if not session_hash:
        raise ValueError("No active session found")

    # Always get all columns from the database first
    try:
        table_name, all_columns, _ = get_table_data(session_hash)
        logger.info(f"Retrieved {len(all_columns)} columns from database table {table_name}")
    except Exception as e:
        logger.error(f"Could not retrieve columns from database: {e}")
        raise ValueError(f"Failed to get columns from database: {str(e)}")

    # Check if a mapping file already exists
    existing_mapping = None
    try:
        existing_mapping = load_mapping(session_hash)
        if existing_mapping and len(existing_mapping) > 0:
            logger.info(f"Found existing mapping file with {len(existing_mapping)} entries")

            # Get schema information for the existing mapping
            schemas = load_schemas()
            schema_name = None
            schema_fields = {}

            # Try to determine which schema this mapping is for
            for column, type_info in existing_mapping.items():
                type_name = type_info.get("type", "")
                for s_name, schema in schemas.items():
                    if type_name in schema.get("schema", {}):
                        schema_name = s_name
                        schema_fields = schema.get("schema", {})
                        break
                if schema_name:
                    break

            if not schema_name and schemas:
                schema_name = next(iter(schemas))
                schema_fields = schemas[schema_name].get("schema", {})

            # Check for required fields
            missing_required = []
            if schema_fields:
                for field_name, field_def in schema_fields.items():
                    if field_def.get("required", False):
                        # Check if this required field has a mapping
                        found = False
                        for column, type_info in existing_mapping.items():
                            if type_info.get("type") == field_name:
                                found = True
                                break
                        if not found:
                            missing_required.append(field_name)

            # Return the existing mapping along with all database columns
            return {
                "mapping_file": os.path.join(get_session_dir(session_hash), "mappings", f"{session_hash}_mapping.json"),
                "mapped_fields": existing_mapping,
                "schema_fields": schema_fields,
                "missing_required": missing_required,
                "all_columns": all_columns  # Include all columns from the database
            }
    except Exception as e:
        logger.warning(f"Error loading existing mapping file: {e}")

    # If no existing mapping or error loading it, proceed with generating a new mapping

    # Get validation results (validate if not done already)
    try:
        # Try to load existing validation results first
        validation_results = load_validation_results(session_hash)
        if not validation_results:
            # If no results, run validation
            validation_results = validate_data()
    except Exception as e:
        logger.warning(f"Error loading validation results, running validation: {e}")
        validation_results = validate_data()

    # Extract field matches and schema
    field_matches = validation_results["field_matches"]
    schema = validation_results["schema"]
    schema_fields = schema.get("schema", {})

    # Create mapping dict
    mapping = {}
    for field_name, match_info in field_matches.items():
        column_name = match_info.get("column")
        if column_name:
            # Get the field definition from the schema to include type information
            field_def = schema_fields.get(field_name, {})
            validate_type = field_def.get("validate_type", "NONE")

            # Create a comprehensive mapping entry with all schema field properties
            mapping_entry = create_mapping_entry(field_name, field_def)

            # Store the mapping entry for this column
            mapping[column_name] = mapping_entry

            # Log the mapping that's being created
            logger.debug(f"Mapped column '{column_name}' to schema type '{field_name}' with validation '{validate_type}'")

    # Check for required fields that aren't mapped
    missing_required = []
    for field_name, field_def in schema_fields.items():
        if field_def.get("required", False):
            # Check if this required field has a mapping
            found = False
            for column, type_info in mapping.items():
                if type_info.get("type") == field_name:
                    found = True
                    break
            if not found:
                missing_required.append(field_name)

    if missing_required:
        logger.warning(f"Missing mappings for required fields: {', '.join(missing_required)}")

    # Save mapping to file
    try:
        session_dir = get_session_dir(session_hash)
        mappings_dir = os.path.join(session_dir, "mappings")

        try:
            os.makedirs(mappings_dir, exist_ok=True)
        except OSError as e:
            logger.error(f"Failed to create mappings directory: {e}")
            raise

        mapping_file = os.path.join(mappings_dir, f"{session_hash}_mapping.json")

        try:
            with open(mapping_file, 'w') as f:
                json.dump(mapping, f, indent=2)

            logger.info(f"Generated mapping file: {mapping_file}")
        except (OSError, IOError) as e:
            logger.error(f"Failed to write mapping file: {e}")
            raise
    except Exception as e:
        logger.error(f"Error in file operations: {e}")
        raise ValueError(f"Failed to save mapping file: {str(e)}")

    # Update session status
    update_session_status(
        session_hash,
        file_path="",  # We don't need to update the file path
        operation="GENERATE_MAPPING"
    )

    # Log mapping generation
    html_logger = HTMLLogger(session_hash)
    html_logger.log_mapping(
        mapping_file=mapping_file,
        mapped_fields=mapping,
        schema_fields=schema_fields
    )

    # Get all columns from the database to include in the response
    try:
        # We already imported get_table_data at the top of the file
        table_name, all_columns, _ = get_table_data(session_hash)
        logger.info(f"Retrieved {len(all_columns)} columns from database table {table_name}")
    except Exception as e:
        logger.warning(f"Could not retrieve all columns from database: {e}")
        all_columns = []

    return {
        "mapping_file": mapping_file,
        "mapped_fields": mapping,
        "schema_fields": schema_fields,
        "missing_required": missing_required,
        "all_columns": all_columns  # Include all columns from the database
    }


def load_mapping(session_hash: Optional[str] = None) -> Dict[str, Any]:
    """
    Load a field mapping file for a session.

    Args:
        session_hash: Hash of the session to load mapping for, or None to use current session

    Returns:
        Dict mapping column names to mapping information
    """
    try:
        if not session_hash:
            session_hash = get_current_session()
            if not session_hash:
                raise ValueError("No active session found")

        session_dir = get_session_dir(session_hash)
        mapping_file = os.path.join(session_dir, "mappings", f"{session_hash}_mapping.json")

        if not os.path.isfile(mapping_file):
            logger.warning(f"Mapping file not found: {mapping_file}")
            return {}

        try:
            with open(mapping_file, 'r') as f:
                try:
                    mapping = json.load(f)
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON in mapping file {mapping_file}: {e}")
                    return {}

            # Handle legacy format where mapping is just strings
            # Convert to new format with column and type
            updated_mapping = {}
            for column_name, value in mapping.items():
                if isinstance(value, str):
                    # Legacy format, just column name
                    updated_mapping[column_name] = {
                        "type": value
                    }
                else:
                    # Already in new format
                    updated_mapping[column_name] = value

            return updated_mapping
        except (OSError, IOError) as e:
            logger.error(f"Failed to read mapping file {mapping_file}: {e}")
            return {}
    except Exception as e:
        logger.error(f"Unexpected error in load_mapping: {e}")
        return {}


def load_validation_results(session_hash: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Try to load existing validation results for a session.

    Args:
        session_hash: Hash of the session to load results for, or None to use current session

    Returns:
        Dict with validation results or None if not found
    """
    if not session_hash:
        session_hash = get_current_session()
        if not session_hash:
            return None

    session_dir = get_session_dir(session_hash)

    # Try to find the most recent validation file
    logs_dir = os.path.join(session_dir, "logs")
    if not os.path.isdir(logs_dir):
        return None

    validation_files = [f for f in os.listdir(logs_dir) if f.startswith("validate_") and not f.startswith("validate_row_")]

    if not validation_files:
        return None

    # Sort by modification time (newest first)
    validation_files.sort(key=lambda f: os.path.getmtime(os.path.join(logs_dir, f)), reverse=True)

    # This is a simplification - in a real system, we would parse the HTML
    # to extract structured data, or store the validation results in a separate JSON file

    # For now, we'll just return a placeholder and let validate_data() run again
    return None


def update_mapping(field_updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Update the field mapping file with user-provided changes.

    Args:
        field_updates: Dict containing field updates from the frontend

    Returns:
        Dict containing updated mapping information
    """
    # Get current session
    session_hash = get_current_session()
    if not session_hash:
        raise ValueError("No active session found")

    # Load existing mapping
    current_mapping = load_mapping(session_hash)

    # Extract field_updates if it's wrapped
    if 'field_updates' in field_updates:
        logger.info("Extracting field_updates from wrapper")
        field_updates = field_updates['field_updates']

    # Process the frontend's format: {"Column Name": {"type": "FIELD_TYPE", ...}}
    for column_name, update in field_updates.items():
        if isinstance(update, dict) and 'type' in update:
            field_type = update['type']
            logger.info(f"Mapping column '{column_name}' to field type '{field_type}'")

            # Use the entire update object as the mapping entry
            # This preserves all the properties sent by the frontend
            current_mapping[column_name] = update

    # Save updated mapping
    try:
        session_dir = get_session_dir(session_hash)
        mappings_dir = os.path.join(session_dir, "mappings")

        try:
            os.makedirs(mappings_dir, exist_ok=True)
        except OSError as e:
            logger.error(f"Failed to create mappings directory: {e}")
            raise

        mapping_file = os.path.join(mappings_dir, f"{session_hash}_mapping.json")

        try:
            with open(mapping_file, 'w') as f:
                json.dump(current_mapping, f, indent=2)

            logger.info(f"Updated mapping file: {mapping_file}")
        except (OSError, IOError) as e:
            logger.error(f"Failed to write updated mapping file: {e}")
            raise
    except Exception as e:
        logger.error(f"Error in file operations during update_mapping: {e}")
        raise ValueError(f"Failed to save updated mapping file: {str(e)}")

    # Update session status
    update_session_status(session_hash, "UPDATE_MAPPING")

    # Log the update
    html_logger = HTMLLogger(session_hash)
    html_logger.log_mapping(
        mapping_file=mapping_file,
        mapped_fields=current_mapping,
        schema_fields={}
    )

    return current_mapping


def get_column_for_field(field_name: str, session_hash: Optional[str] = None) -> Optional[str]:
    """
    Get the mapped column name for a field.

    Args:
        field_name: Name of the field to look up
        session_hash: Hash of the session to use, or None for current session

    Returns:
        Column name or None if not mapped
    """
    mapping = load_mapping(session_hash)
    for column, type_info in mapping.items():
        if type_info.get("type") == field_name:
            return column
    return None


def get_field_for_column(column_name: str, session_hash: Optional[str] = None) -> Optional[str]:
    """
    Get the field type for a column.

    Args:
        column_name: Name of the column to look up
        session_hash: Hash of the session to use, or None for current session

    Returns:
        Field type name or None if not mapped
    """
    mapping = load_mapping(session_hash)
    type_info = mapping.get(column_name, {})
    return type_info.get("type")


def delete_mapping_file() -> Dict[str, Any]:
    """
    Delete the field mapping file for the current session.

    Returns:
        Dict with status of the operation

    Raises:
        ValueError: If no active session found
    """
    # Get current session
    session_hash = get_current_session()
    if not session_hash:
        raise ValueError("No active session found")

    # Get path to mapping file
    session_dir = get_session_dir(session_hash)
    mapping_path = os.path.join(session_dir, "mappings", f"{session_hash}_mapping.json")

    # Check if mapping file exists
    if not os.path.isfile(mapping_path):
        logger.warning(f"No mapping file found at {mapping_path}")
        return {"status": "not_found", "message": "No mapping file found"}

    try:
        # Create a backup before deleting
        backup_path = f"{mapping_path}.bak"
        logger.info(f"Creating backup of mapping file at {backup_path}")
        if not os.path.exists(os.path.dirname(backup_path)):
            os.makedirs(os.path.dirname(backup_path), exist_ok=True)
        shutil.copy2(mapping_path, backup_path)

        # Delete the file
        os.remove(mapping_path)
        logger.info(f"Deleted mapping file: {mapping_path}")

        # Update session status
        update_session_status(
            session_hash,
            file_path="",
            operation="DELETE_MAPPING"
        )

        return {"status": "success", "message": "Mapping file deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting mapping file: {e}")
        return {"status": "error", "message": f"Error deleting mapping file: {str(e)}"}