#!/usr/bin/env python
"""
Lookup Resolver - Implement Phase 2 Lookup Resolution for generated documents.

This module handles the lookup resolution process, matching generated document records
to foreign keys through the specified mapping types.
"""

import os
import json
import logging
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import time

from core.session import get_current_session, get_session_dir, load_config
from core.importer import get_table_data

# Configure logging
logger = logging.getLogger(__name__)


def resolve_lookups(session_hash: Optional[str] = None) -> Dict[str, Any]:
    """
    Resolve lookups for all unresolved records in generated_{table_hash}.
    
    This function implements Phase 2 of the document generation process,
    where lookups are performed to match generated documents with foreign keys.
    
    Args:
        session_hash: Session hash, if None uses current session
        
    Returns:
        Dict containing resolution results
    
    Raises:
        ValueError: If no active session found
        RuntimeError: If lookup resolution fails
    """
    # Get current session if not provided
    if not session_hash:
        session_hash = get_current_session()
    if not session_hash:
        raise ValueError("No active session found")
    
    # Get the table hash and session directory
    table_hash, _, _ = get_table_data(session_hash)
    session_dir = get_session_dir(session_hash)
    
    # Initialize database connection
    db_path = os.path.join(session_dir, "data.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Table names
    generated_table_name = f"generated_{table_hash}"
    lookup_table_name = f"tenant_lookup_{table_hash}"
    exceptions_table_name = f"tenant_lookup_exceptions_{table_hash}"
    
    # Ensure required tables exist
    _ensure_tables_exist(cursor, generated_table_name, lookup_table_name, exceptions_table_name)
    conn.commit()
    
    # Get document type from status.json
    try:
        with open("status.json", 'r') as f:
            status = json.load(f)
            document_type = status.get("current_state", {}).get("document_type")
            input_file = status.get("current_state", {}).get("imported_file", "")
    except (json.JSONDecodeError, FileNotFoundError) as e:
        logger.error(f"Error reading status.json: {e}")
        raise ValueError("Document type not found in status.json")
    
    if not document_type:
        raise ValueError("Document type not found in status.json")
    
    # Load tenant mappings
    tenant_mappings = _load_tenant_mappings(document_type)
    
    # Get unresolved records
    cursor.execute(
        f"SELECT id, document_type, mime_type, input_file, row, data FROM {generated_table_name} "
        f"WHERE lookup_type IS NULL"
    )
    unresolved_records = cursor.fetchall()
    
    if not unresolved_records:
        logger.info("No unresolved records found")
        conn.close()
        return {
            "status": "success",
            "message": "No unresolved records found",
            "records_processed": 0,
            "successful_lookups": 0,
            "exceptions": 0
        }
    
    logger.info(f"Found {len(unresolved_records)} unresolved records")
    
    # Process each unresolved record
    successful_lookups = 0
    exceptions = 0
    
    for record in unresolved_records:
        record_id, doc_type, mime_type, input_file, row_num, data_json = record
        
        try:
            data = json.loads(data_json)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON data for record {record_id}")
            exceptions += 1
            _log_exception(
                cursor,
                exceptions_table_name,
                "Invalid JSON data",
                f"Failed to parse data JSON for record {record_id}",
                input_file,
                row_num,
                data_json
            )
            continue
        
        # Determine lookup methods to try
        lookup_methods = []
        if "column_to_column" in tenant_mappings:
            lookup_methods.append("column_to_column")
        if "type_to_column" in tenant_mappings:
            lookup_methods.append("type_to_column")
        
        if not lookup_methods:
            logger.warning(f"No lookup methods defined for document type {document_type}")
            exceptions += 1
            _log_exception(
                cursor,
                exceptions_table_name,
                "No lookup methods defined",
                f"No column_to_column or type_to_column mappings found for {document_type}",
                input_file,
                row_num,
                data_json
            )
            continue
        
        # Try each lookup method
        lookup_successful = False
        
        for lookup_type in lookup_methods:
            mappings = tenant_mappings.get(lookup_type, [])
            
            for mapping in mappings:
                # Log the lookup attempt
                action = f"Trying {lookup_type} mapping: {mapping}"
                lookup_attempt_id = _log_lookup_attempt(cursor, lookup_table_name, record_id, action)
                
                try:
                    # Attempt the lookup
                    result = _perform_lookup(cursor, lookup_type, mapping, data, table_hash)
                    
                    if result:
                        # Successful lookup
                        lookup_value, lookup_match = result
                        
                        # Update the generated record
                        _update_generated_record(
                            cursor, 
                            generated_table_name, 
                            record_id, 
                            lookup_type, 
                            mapping, 
                            lookup_match, 
                            lookup_value
                        )
                        
                        successful_lookups += 1
                        lookup_successful = True
                        logger.info(f"Successful lookup for record {record_id} using {lookup_type}")
                        break  # Stop trying other mappings
                    
                except Exception as e:
                    # Log the exception
                    logger.error(f"Error during lookup: {e}")
                    exception_id = _log_exception(
                        cursor,
                        exceptions_table_name,
                        f"Error during {lookup_type} lookup",
                        str(e),
                        input_file,
                        row_num,
                        data_json
                    )
                    
                    # Update the lookup attempt with the exception ID
                    cursor.execute(
                        f"UPDATE {lookup_table_name} SET tenant_lookup_exceptions_id = ? WHERE id = ?",
                        (exception_id, lookup_attempt_id)
                    )
            
            if lookup_successful:
                break  # Stop trying other lookup types
        
        if not lookup_successful:
            exceptions += 1
            logger.warning(f"No successful lookup for record {record_id}")
    
    # Commit all changes
    conn.commit()
    conn.close()
    
    return {
        "status": "success",
        "records_processed": len(unresolved_records),
        "successful_lookups": successful_lookups,
        "exceptions": exceptions
    }


def _ensure_tables_exist(cursor, generated_table_name, lookup_table_name, exceptions_table_name):
    """Ensure all required tables exist."""
    # Check for generated_{table_hash}
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{generated_table_name}'")
    if cursor.fetchone() is None:
        raise ValueError(f"Table {generated_table_name} not found. Run Phase 1 (document generation) first.")
    
    # Create tenant_lookup_{table_hash} if not exists
    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS {lookup_table_name} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        generated_id INTEGER NOT NULL,
        action TEXT NOT NULL,
        tenant_lookup_exceptions_id INTEGER,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create tenant_lookup_exceptions_{table_hash} if not exists
    cursor.execute(f'''
    CREATE TABLE IF NOT EXISTS {exceptions_table_name} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        action TEXT NOT NULL,
        exception_message TEXT NOT NULL,
        input_file TEXT NOT NULL,
        row INTEGER NOT NULL,
        data TEXT NOT NULL,
        accept_action INTEGER DEFAULT NULL,
        lookup_value TEXT,
        status INTEGER DEFAULT 0,
        created_at INTEGER NOT NULL,
        updated_at INTEGER
    )
    ''')


def _load_tenant_mappings(document_type):
    """Load tenant mappings for the specified document type."""
    tenant_mappings = {}
    
    try:
        # Load from config
        config = load_config()
        tenant = config.get("tenant", {})
        mappings = tenant.get("mappings", {}).get(document_type, {})
        
        if "column_to_column" in mappings:
            tenant_mappings["column_to_column"] = mappings["column_to_column"]
        
        if "type_to_column" in mappings:
            tenant_mappings["type_to_column"] = mappings["type_to_column"]
        
    except Exception as e:
        logger.error(f"Error loading tenant mappings: {e}")
    
    return tenant_mappings


def _log_lookup_attempt(cursor, lookup_table_name, generated_id, action):
    """Log a lookup attempt and return the attempt ID."""
    cursor.execute(
        f"INSERT INTO {lookup_table_name} (generated_id, action) VALUES (?, ?)",
        (generated_id, action)
    )
    return cursor.lastrowid


def _log_exception(cursor, exceptions_table_name, action, exception_message, input_file, row, data):
    """Log a lookup exception and return the exception ID."""
    current_time = int(time.time())
    
    cursor.execute(
        f"INSERT INTO {exceptions_table_name} "
        f"(action, exception_message, input_file, row, data, created_at) "
        f"VALUES (?, ?, ?, ?, ?, ?)",
        (action, exception_message, input_file, row, data, current_time)
    )
    
    return cursor.lastrowid


def _update_generated_record(cursor, generated_table_name, record_id, lookup_type, lookup, lookup_match, lookup_value):
    """Update a generated record with lookup information."""
    cursor.execute(
        f"UPDATE {generated_table_name} "
        f"SET lookup_type = ?, lookup = ?, lookup_match = ?, lookup_value = ? "
        f"WHERE id = ?",
        (lookup_type, lookup, lookup_match, lookup_value, record_id)
    )


def _perform_lookup(cursor, lookup_type, mapping, data, table_hash):
    """
    Perform a lookup based on mapping type and configuration.
    
    Returns:
        Tuple of (lookup_value, lookup_match) if successful, None otherwise
    """
    if lookup_type == "column_to_column":
        return _perform_column_to_column_lookup(cursor, mapping, data, table_hash)
    elif lookup_type == "type_to_column":
        return _perform_type_to_column_lookup(cursor, mapping, data, table_hash)
    else:
        return None


def _perform_column_to_column_lookup(cursor, mapping, data, table_hash):
    """Perform a column-to-column lookup."""
    # Parse the mapping
    # Example: "local_sqlite:imported_ce65e00a45:'Shareholder ID Number' = local_mysql:users:email"
    try:
        source_side, dest_side = mapping.split('=')
        source_side = source_side.strip()
        dest_side = dest_side.strip()
        
        source_parts = source_side.split(':')
        dest_parts = dest_side.split(':')
        
        if len(source_parts) < 3 or len(dest_parts) < 3:
            logger.error(f"Invalid mapping format: {mapping}")
            return None
        
        # Extract connection, table, and column
        source_conn = source_parts[0]
        source_table = source_parts[1]
        source_column = source_parts[2].strip("'\"")
        
        dest_conn = dest_parts[0]
        dest_table = dest_parts[1]
        dest_column = dest_parts[2]
        
        # Find the source value in the data
        source_value = None
        for key, value in data.items():
            if key == source_column:
                source_value = value
                break
        
        if source_value is None:
            logger.warning(f"Source column '{source_column}' not found in data")
            return None
        
        # Query destination based on connection type
        if dest_conn == "local_sqlite":
            return _query_local_sqlite(cursor, dest_table, dest_column, source_value)
        elif dest_conn == "local_mysql":
            return _query_local_mysql(dest_table, dest_column, source_value)
        else:
            logger.warning(f"Unsupported destination connection: {dest_conn}")
            return None
        
    except Exception as e:
        logger.error(f"Error parsing mapping '{mapping}': {e}")
        return None


def _perform_type_to_column_lookup(cursor, mapping, data, table_hash):
    """Perform a type-to-column lookup."""
    # Parse the mapping
    # Example: "local_sqlite:imported_ce65e00a45:SA_ID_NUMBER = local_mysql:users:email"
    try:
        source_side, dest_side = mapping.split('=')
        source_side = source_side.strip()
        dest_side = dest_side.strip()
        
        source_parts = source_side.split(':')
        dest_parts = dest_side.split(':')
        
        if len(source_parts) < 3 or len(dest_parts) < 3:
            logger.error(f"Invalid mapping format: {mapping}")
            return None
        
        # Extract connection, table, and type
        source_conn = source_parts[0]
        source_table = source_parts[1]
        source_type = source_parts[2]
        
        dest_conn = dest_parts[0]
        dest_table = dest_parts[1]
        dest_column = dest_parts[2]
        
        # Find the source value in data based on type
        source_value = None
        for key, value in data.items():
            # In a real system, you would check the field type here
            # For this example, we'll use a simple string match
            if key == source_type:
                source_value = value
                break
        
        if source_value is None:
            logger.warning(f"Field with type '{source_type}' not found in data")
            return None
        
        # Query destination based on connection type
        if dest_conn == "local_sqlite":
            return _query_local_sqlite(cursor, dest_table, dest_column, source_value)
        elif dest_conn == "local_mysql":
            return _query_local_mysql(dest_table, dest_column, source_value)
        else:
            logger.warning(f"Unsupported destination connection: {dest_conn}")
            return None
        
    except Exception as e:
        logger.error(f"Error parsing mapping '{mapping}': {e}")
        return None


def _query_local_sqlite(cursor, table, column, value):
    """Query a local SQLite database."""
    try:
        # Execute the query
        query = f"SELECT {column} FROM {table} WHERE {column} = ?"
        cursor.execute(query, (value,))
        
        # Check results
        results = cursor.fetchall()
        
        if not results:
            logger.warning(f"No matches found in {table}.{column} for value '{value}'")
            return None
        
        if len(results) > 1:
            logger.warning(f"Multiple matches found in {table}.{column} for value '{value}'")
            raise ValueError(f"Multiple matches found in {table}.{column}")
        
        # Single match found
        lookup_value = results[0][0]
        lookup_match = f"{value}:{lookup_value}"
        
        return lookup_value, lookup_match
        
    except Exception as e:
        logger.error(f"Error querying SQLite: {e}")
        raise


def _query_local_mysql(table, column, value):
    """Query a local MySQL database."""
    # This is a placeholder - in a real implementation, you'd connect to MySQL
    # For this example, we'll just simulate a lookup
    logger.info(f"Simulating MySQL query on {table}.{column} for value '{value}'")
    
    # Simulate a successful lookup
    lookup_value = f"mysql-{value}"
    lookup_match = f"{value}:{lookup_value}"
    
    return lookup_value, lookup_match


def resolve_exception(session_hash: str, exception_id: int, accept: bool, lookup_value: Optional[str] = None) -> Dict[str, Any]:
    """
    Resolve a lookup exception.
    
    Args:
        session_hash: Session hash
        exception_id: Exception ID to resolve
        accept: Whether to accept the exception
        lookup_value: Lookup value to use if accepting (required if accept=True)
        
    Returns:
        Dict with resolution results
    """
    # Get the table hash
    table_hash, _, _ = get_table_data(session_hash)
    session_dir = get_session_dir(session_hash)
    
    # Initialize database connection
    db_path = os.path.join(session_dir, "data.db")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Table names
    generated_table_name = f"generated_{table_hash}"
    exceptions_table_name = f"tenant_lookup_exceptions_{table_hash}"
    
    # Get the exception record
    cursor.execute(
        f"SELECT action, input_file, row, data, accept_action, status FROM {exceptions_table_name} WHERE id = ?",
        (exception_id,)
    )
    exception_record = cursor.fetchone()
    
    if not exception_record:
        conn.close()
        return {
            "status": "error",
            "message": f"Exception with ID {exception_id} not found"
        }
    
    action, input_file, row, data_json, current_accept_action, current_status = exception_record
    
    # Check if already resolved
    if current_status == 1:
        conn.close()
        return {
            "status": "error",
            "message": f"Exception with ID {exception_id} is already resolved"
        }
    
    # Update exception record
    current_time = int(time.time())
    accept_action_value = 1 if accept else 0
    
    if accept and not lookup_value:
        conn.close()
        return {
            "status": "error",
            "message": "Lookup value is required when accepting an exception"
        }
    
    # Update the exception record
    cursor.execute(
        f"UPDATE {exceptions_table_name} "
        f"SET accept_action = ?, status = 1, lookup_value = ?, updated_at = ? "
        f"WHERE id = ?",
        (accept_action_value, lookup_value if accept else None, current_time, exception_id)
    )
    
    # If accepting, update the generated record
    if accept:
        # Find the record in generated_{table_hash} based on input_file and row
        cursor.execute(
            f"SELECT id FROM {generated_table_name} WHERE input_file = ? AND row = ?",
            (input_file, row)
        )
        record = cursor.fetchone()
        
        if record:
            record_id = record[0]
            
            # Update the record with lookup information
            cursor.execute(
                f"UPDATE {generated_table_name} "
                f"SET lookup_type = 'manual_resolution', "
                f"lookup = 'manually_resolved', "
                f"lookup_match = 'manually_matched', "
                f"lookup_value = ? "
                f"WHERE id = ?",
                (lookup_value, record_id)
            )
    
    # Commit and close
    conn.commit()
    conn.close()
    
    return {
        "status": "success",
        "message": f"Exception {exception_id} resolved with action: {'accept' if accept else 'reject'}"
    }
