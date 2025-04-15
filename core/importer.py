#!/usr/bin/env python
"""
Data Importer - Import Excel/CSV files and store them in SQLite.

"""

import os
import sqlite3
import logging
import pandas as pd
from typing import Dict, List, Any, Tuple, Optional
from pathlib import Path
import datetime
import json

from core.session import (
    compute_file_hash,
    create_output_dir,
    update_session_status,
    get_session_dir,
    get_current_session
)
from core.logger import HTMLLogger

# Configure logging
logger = logging.getLogger(__name__)


def detect_encoding(file_path: str) -> str:
    """
    Detect the encoding of a text file using chardet.

    Args:
        file_path: Path to the file

    Returns:
        Detected encoding or 'utf-8' as fallback
    """
    try:
        import chardet
        with open(file_path, 'rb') as f:
            raw_data = f.read(4096)  # Read a chunk for detection
            if not raw_data:
                return 'utf-8'

            result = chardet.detect(raw_data)
            encoding = result['encoding']
            confidence = result['confidence']

            logger.info(f"Detected encoding: {encoding} (confidence: {confidence:.2f})")

            return encoding or 'utf-8'
    except ImportError:
        logger.warning("chardet module not installed, defaulting to utf-8")
        return 'utf-8'
    except Exception as e:
        logger.warning(f"Error detecting encoding: {e}, defaulting to utf-8")
        return 'utf-8'

def convert_to_utf8_with_lf(file_path: str) -> Dict[str, Any]:
    """
    Convert a file to UTF-8 encoding with Unix line endings (LF).
    Creates a temporary file for processing.

    Args:
        file_path: Path to the file to convert

    Returns:
        Dict with conversion information and new file path
    """
    original_encoding = detect_encoding(file_path)
    file_name = os.path.basename(file_path)
    file_dir = os.path.dirname(file_path)

    # Create a temporary file with _utf8 suffix
    temp_file_path = os.path.join(file_dir, f"{os.path.splitext(file_name)[0]}_utf8{os.path.splitext(file_name)[1]}")

    line_ending_changes = 0
    converted = False

    try:
        with open(file_path, 'rb') as src_file:
            content = src_file.read()

        # Check if we need conversion
        try:
            text = content.decode(original_encoding)

            # Count Windows line endings (CRLF)
            crlf_count = text.count('\r\n')

            # Replace CRLF with LF
            if crlf_count > 0:
                text = text.replace('\r\n', '\n')
                line_ending_changes = crlf_count

            # Only write a new file if encoding needs to change or line endings were modified
            if original_encoding.lower() != 'utf-8' or line_ending_changes > 0:
                with open(temp_file_path, 'w', encoding='utf-8', newline='\n') as dest_file:
                    dest_file.write(text)
                converted = True
                logger.info(f"Converted {file_path} from {original_encoding} to UTF-8 with Unix line endings")
            else:
                # No conversion needed
                temp_file_path = file_path
                logger.info(f"No encoding conversion needed for {file_path} (already UTF-8 with Unix line endings)")
        except UnicodeDecodeError as e:
            logger.error(f"Error decoding file {file_path} with encoding {original_encoding}: {e}")
            temp_file_path = file_path  # Fall back to original
    except Exception as e:
        logger.error(f"Error converting file encoding: {e}")
        temp_file_path = file_path  # Fall back to original

    return {
        "original_path": file_path,
        "converted_path": temp_file_path,
        "original_encoding": original_encoding,
        "new_encoding": "utf-8" if converted else original_encoding,
        "line_ending_changes": line_ending_changes,
        "converted": converted
    }

def import_file(file_path: str) -> Dict[str, Any]:
    """
    Import a CSV or Excel file into SQLite.
    Handles large files efficiently using batch processing.

    Args:
        file_path: Path to the file to import

    Returns:
        Dict containing import information

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file format is unsupported
        DatabaseError: If database operations fail
    """
    # Validate file path
    if not os.path.isfile(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    # Determine file extension
    file_ext = os.path.splitext(file_path)[1].lower()

    # Convert file to UTF-8 with Unix line endings if needed
    conversion_info = convert_to_utf8_with_lf(file_path)
    file_path = conversion_info["converted_path"]

    # Compute file hash - this sets our session ID
    file_hash = compute_file_hash(file_path)
    logger.info(f"Computed file hash: {file_hash}")

    # Create output directory structure
    create_output_dir(file_hash)
    session_dir = get_session_dir(file_hash)

    # Create database path
    db_path = os.path.join(session_dir, "data.db")

    # Read the file metadata first to get column info
    try:
        # Initialize table_name outside the if/elif block
        table_name = None
        if file_ext == '.csv':
            # Try to detect encoding
            encoding = detect_encoding(file_path)

            # Connect to SQLite database
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Drop table if it exists (force reimport)
            table_name = f"imported_{file_hash[:10]}"
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")

            # Read the first few rows to get column info
            df_sample = pd.read_csv(file_path, nrows=5, dtype=str, encoding=encoding, sep=';')

            # Create sanitized column names
            original_columns = list(df_sample.columns)
            sanitized_columns = [sanitize_column_name(col) for col in original_columns]

            # Create column mapping for later use
            column_mapping = dict(zip(original_columns, sanitized_columns))

            # Create table with sanitized column names
            create_table_sql = f"CREATE TABLE {table_name} ("
            create_table_sql += "id INTEGER PRIMARY KEY AUTOINCREMENT, "
            create_table_sql += ", ".join([f'"{col}" TEXT' for col in sanitized_columns])
            create_table_sql += ")"

            cursor.execute(create_table_sql)

            # Create prepared statement for insertions with sanitized column names
            placeholders = ", ".join(["?"] * len(sanitized_columns))
            quoted_columns = [f'"{col}"' for col in sanitized_columns]
            insert_sql = f'INSERT INTO {table_name} ({", ".join(quoted_columns)}) VALUES ({placeholders})'

            # Process CSV in chunks with sanitized column names
            chunk_size = 10000  # Adjust based on memory requirements
            total_rows = 0

            for chunk in pd.read_csv(file_path, chunksize=chunk_size, dtype=str, encoding=encoding, sep=';'):
                # Rename columns to sanitized versions
                chunk.columns = [sanitize_column_name(col) for col in chunk.columns]
                # Replace NaN with empty string
                chunk = chunk.fillna('')
                # Convert to list of lists for SQL insertion
                chunk_rows = chunk.values.tolist()
                # Insert data
                cursor.executemany(insert_sql, chunk_rows)
                total_rows += len(chunk_rows)
                logger.debug(f"Imported {total_rows} rows so far...")

            conn.commit()

        elif file_ext in ['.xlsx', '.xls']:
            # Similar approach for Excel, but using different pandas method
            # Excel files are typically smaller, so we might handle them all at once
            df = pd.read_excel(file_path, dtype=str)
            df = df.fillna('')
            columns = list(df.columns)
            total_rows = len(df)

            # Connect to SQLite
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            # Create table
            table_name = f"imported_{file_hash[:10]}"
            df.to_sql(table_name, conn, if_exists='replace', index=False)

        else:
            raise ValueError(f"Unsupported file format: {file_ext}")

        # Create import_meta table if not exists
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS import_meta (
                id INTEGER PRIMARY KEY AUTOINCREMENT ,
                file_name TEXT,
                file_hash TEXT,
                row_count INTEGER,
                column_count INTEGER,
                column_names TEXT,
                document_type TEXT,
                created_at TEXT)""")

        # Insert metadata into import_meta
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if file_ext == '.csv':
            cursor.execute("""
                INSERT INTO import_meta (file_name, file_hash, row_count, column_count, column_names, document_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""", (
                os.path.basename(file_path),
                file_hash,
                total_rows,
                len(sanitized_columns),
                json.dumps(sanitized_columns),  # Store columns as JSON string
                None,  # Document type initially null
                now))
        else:
            cursor.execute("""
                INSERT INTO import_meta (file_name, file_hash, row_count, column_count, column_names, document_type, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)""", (
                os.path.basename(file_path),
                file_hash,
                total_rows,
                len(columns),
                json.dumps(columns),  # Store columns as JSON string
                None,  # Document type initially null
                now))

        conn.commit()


    except Exception as e:
        logger.error(f"Error importing file {file_path}: {e}")

        if 'conn' in locals():
            conn.rollback()
        raise
    finally:
        if 'conn' in locals():
            conn.close()

    # Update session status
    update_session_status(file_hash, file_path)

    # Generate import log
    html_logger = HTMLLogger(file_hash)
    # Get sample data for the log (top 10 rows)
    current_year = datetime.datetime.now().year
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    sample_data = []
    if table_name:
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 10")
        sample_data = [dict(row) for row in cursor.fetchall()]
        conn.close()

    html_logger.log_import(
        file_path=file_path,
        table_name=table_name,
        num_rows=total_rows,
        columns=sanitized_columns if file_ext == '.csv' else columns,
        sample_data=sample_data,
        current_year=current_year,
        conversion_info=conversion_info
    )

    # Return import information
    if file_ext == '.csv':
        return {
            "hash": file_hash,
            "file_path": file_path,
            "table_name": table_name,
            "num_rows": total_rows,
            "columns": sanitized_columns,
            "db_path": db_path,
            "session_dir": session_dir
        }
    else:
        return {
            "hash": file_hash,
            "file_path": file_path,
            "table_name": table_name,
            "num_rows": total_rows,
            "columns": columns,
            "db_path": db_path,
            "session_dir": session_dir
        }

def sanitize_column_name(name: str) -> str:
    """
    Sanitize column name to prevent SQL injection.

    Args:
        name: Original column name

    Returns:
        Sanitized column name
    """
    # Remove dangerous characters
    return name.replace('"', '').replace("'", "").replace(";", "")


def get_table_data(session_hash: Optional[str] = None) -> Tuple[str, List[str], List[Dict[str, Any]]]:
    """
    Get data from the imported table for the current session.

    Args:
        session_hash: Hash of the session to get data for, or None to use current session

    Returns:
        Tuple of (table_name, columns, data)
    """
    if not session_hash:
        session_hash = get_current_session()
        if not session_hash:
            raise ValueError("No active session found")

    # Get the database path from status.json
    try:
        with open('status.json', 'r') as f:
            status_data = json.load(f)

        # Check if the current session matches the one in status.json
        current_state = status_data.get('current_state', {})
        if current_state.get('hash') == session_hash and 'sqlite_db_file' in current_state:
            db_path = current_state['sqlite_db_file']
            logger.info(f"Using database path from status.json: {db_path}")
        else:
            # Fallback to the default path
            session_dir = get_session_dir(session_hash)
            db_path = os.path.join(session_dir, "data.db")
            logger.info(f"Using default database path: {db_path}")
    except Exception as e:
        # Fallback to the default path if status.json can't be read
        logger.warning(f"Could not read database path from status.json: {e}")
        session_dir = get_session_dir(session_hash)
        db_path = os.path.join(session_dir, "data.db")

    # Make sure the database file exists
    if not os.path.isfile(db_path):
        logger.error(f"Database file not found: {db_path}")
        raise FileNotFoundError(f"Database file not found: {db_path}")

    # Connect to the database
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
    except sqlite3.Error as e:
        logger.error(f"Error connecting to database {db_path}: {e}")
        raise

    try:
        # Get the table name
        cursor = conn.cursor()

        # Extract the first 10 characters of the session hash to match the table name pattern
        hash_prefix = session_hash[:10]
        exact_table_name = f"imported_{hash_prefix}"

        # First try to find the exact table
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = ?", (exact_table_name,))
        table_result = cursor.fetchone()

        if not table_result:
            # If exact match not found, fall back to the old method
            logger.warning(f"Exact table {exact_table_name} not found, trying pattern match")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name = 'imported_' || ? ", (hash_prefix,))
            table_result = cursor.fetchone()

            if not table_result:
                logger.error(f"No imported table found in database {db_path}")
                raise ValueError(f"No imported table found in database {db_path}")

        table_name = table_result[0]
        logger.info(f"Using table: {table_name}")

        # Get the columns
        cursor.execute(f"PRAGMA table_info({table_name})")
        columns = [row['name'] for row in cursor.fetchall() if row['name'] != 'id']

        if not columns:
            logger.warning(f"No columns found in table {table_name}")

        # Get the data
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        data = [dict(row) for row in rows]

        logger.info(f"Retrieved {len(data)} rows from table {table_name} with {len(columns)} columns")
        return table_name, columns, data

    except Exception as e:
        logger.error(f"Error retrieving data from SQLite: {e}")
        raise

    finally:
        conn.close()


def get_column_info(session_hash: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
    """
    Get information about columns in the imported data.

    Args:
        session_hash: Hash of the session to get data for, or None to use current session

    Returns:
        Dict mapping column names to column information
    """
    table_name, columns, data = get_table_data(session_hash)

    # Initialize column info
    column_info = {}

    # Analyze each column
    for col in columns:
        # Extract values for this column
        values = [row.get(col, '') for row in data if col in row]

        # Count non-empty values
        non_empty = sum(1 for v in values if v)

        # Calculate fill rate
        fill_rate = (non_empty / len(values) * 100) if values else 0

        # Get sample values (up to 5)
        sample_values = [v for v in values if v][:5]

        # Store column info
        column_info[col] = {
            "name": col,
            "count": len(values),
            "non_empty": non_empty,
            "fill_rate": fill_rate,
            "sample_values": sample_values
        }

    return column_info
