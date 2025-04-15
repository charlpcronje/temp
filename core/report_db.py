#!/usr/bin/env python
"""
Report Database Manager - Handle database operations for the reporting system.
"""

import os
import sqlite3
import json
import logging
import hashlib
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path

from core.session import get_current_session, get_session_dir

# Configure logging
logger = logging.getLogger(__name__)

def init_reporting_db(session_hash: Optional[str] = None) -> sqlite3.Connection:
    """
    Initialize the reporting database tables for storing report metadata.
    
    Args:
        session_hash: Hash identifying the session, or None to use current session
        
    Returns:
        SQLite connection object
    """
    if not session_hash:
        session_hash = get_current_session()
        if not session_hash:
            raise ValueError("No active session found. Please import a file first.")
    
    # Get session directory and database path
    session_dir = get_session_dir(session_hash)
    db_path = os.path.join(session_dir, "data.db")
    
    # Ensure the database file exists
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Database file not found at {db_path}")
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    
    # Create the report_runs table if it doesn't exist
    conn.execute('''
    CREATE TABLE IF NOT EXISTS report_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_id TEXT UNIQUE NOT NULL,
        session_hash TEXT NOT NULL,
        snapshot_table TEXT NOT NULL,
        table_hash TEXT NOT NULL,
        source_file TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Create the lookups_snapshot_reports table if it doesn't exist
    conn.execute('''
    CREATE TABLE IF NOT EXISTS lookups_snapshot_reports (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        report_id TEXT NOT NULL,
        snapshot_table TEXT NOT NULL,
        report_name TEXT NOT NULL,
        report_type TEXT NOT NULL,
        template_used TEXT NOT NULL,
        path TEXT NOT NULL,
        html_file TEXT NOT NULL,
        pdf_file TEXT NOT NULL,
        source_hash TEXT NOT NULL,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Optional: Create the report_templates table for template versioning
    conn.execute('''
    CREATE TABLE IF NOT EXISTS report_templates (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        template_name TEXT NOT NULL,
        version TEXT NOT NULL,
        description TEXT,
        last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    # Commit the changes
    conn.commit()
    logger.info(f"Initialized reporting database tables for session {session_hash}")
    
    return conn

def generate_snapshot_table(conn: sqlite3.Connection, source_table_name: str) -> Tuple[str, str]:
    """
    Duplicates a source table into a snapshot table for report generation.
    
    Args:
        conn: SQLite connection
        source_table_name: Name of the source table to snapshot
        
    Returns:
        Tuple of (snapshot_table_name, table_hash)
    """
    cursor = conn.cursor()
    
    # Check if the source table exists
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{source_table_name}'")
    if not cursor.fetchone():
        raise ValueError(f"Source table '{source_table_name}' does not exist")
    
    # Get the schema of the source table
    cursor.execute(f"PRAGMA table_info({source_table_name})")
    columns = cursor.fetchall()
    if not columns:
        raise ValueError(f"Source table '{source_table_name}' has no columns")
    
    # Calculate the hash of the source table content
    table_hash = calculate_table_hash(conn, source_table_name)
    
    # Create the snapshot table name
    snapshot_table_name = f"lookups_snapshot_{table_hash}"
    
    # Check if the snapshot table already exists
    cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{snapshot_table_name}'")
    if cursor.fetchone():
        logger.info(f"Snapshot table '{snapshot_table_name}' already exists")
        return snapshot_table_name, table_hash
    
    # Generate column definitions string
    column_defs = ', '.join([f'"{col[1]}" {col[2]}' for col in columns])
    
    # Create the snapshot table with the same schema
    create_table_sql = f"CREATE TABLE {snapshot_table_name} ({column_defs})"
    cursor.execute(create_table_sql)
    
    # Copy all data from the source table to the snapshot table
    cursor.execute(f"INSERT INTO {snapshot_table_name} SELECT * FROM {source_table_name}")
    
    # Commit the changes
    conn.commit()
    
    logger.info(f"Created snapshot table '{snapshot_table_name}' from '{source_table_name}'")
    return snapshot_table_name, table_hash

def calculate_table_hash(conn: sqlite3.Connection, table_name: str) -> str:
    """
    Calculate a consistent SHA256 hash of a table's contents.
    
    Args:
        conn: SQLite connection
        table_name: Name of the table to hash
        
    Returns:
        Hexadecimal hash string
    """
    cursor = conn.cursor()
    
    # Get all rows in a consistent order
    cursor.execute(f"SELECT * FROM {table_name} ORDER BY rowid")
    rows = cursor.fetchall()
    
    # Serialize the rows to a JSON string for hashing
    data_str = json.dumps(rows, sort_keys=True)
    
    # Calculate the SHA256 hash
    hash_obj = hashlib.sha256(data_str.encode())
    return hash_obj.hexdigest()[:12]  # Use first 12 chars for brevity

def generate_report_id() -> str:
    """
    Generate a unique report ID.
    
    Returns:
        UUID or hash-based report ID
    """
    # Create a unique identifier based on timestamp and random value
    timestamp = datetime.now().isoformat()
    random_value = os.urandom(8).hex()
    hash_input = f"{timestamp}-{random_value}"
    
    # Calculate SHA256 hash
    hash_obj = hashlib.sha256(hash_input.encode())
    return f"r-{hash_obj.hexdigest()[:8]}"  # Format: r-[8 chars]

def report_table_exists(conn: sqlite3.Connection, report_id: str) -> bool:
    """
    Check if a report with the given ID already exists.
    
    Args:
        conn: SQLite connection
        report_id: Report ID to check
        
    Returns:
        True if the report exists, False otherwise
    """
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM report_runs WHERE report_id = ?", (report_id,))
    return cursor.fetchone() is not None

def record_report_run(
    conn: sqlite3.Connection, 
    report_id: str, 
    session_hash: str, 
    snapshot_table: str, 
    table_hash: str, 
    source_file: str
) -> int:
    """
    Record a report run in the database.
    
    Args:
        conn: SQLite connection
        report_id: Unique ID for the report run
        session_hash: Hash of the session
        snapshot_table: Name of the snapshot table
        table_hash: Hash of the table content
        source_file: Original source file
        
    Returns:
        ID of the inserted row
    """
    cursor = conn.cursor()
    current_time = datetime.now().isoformat()
    
    cursor.execute(
        """
        INSERT INTO report_runs 
        (report_id, session_hash, snapshot_table, table_hash, source_file, created_at, updated_at) 
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (report_id, session_hash, snapshot_table, table_hash, source_file, current_time, current_time)
    )
    
    conn.commit()
    logger.info(f"Recorded report run {report_id} for session {session_hash}")
    return cursor.lastrowid

def record_report_file(
    conn: sqlite3.Connection,
    report_id: str,
    snapshot_table: str,
    report_name: str,
    report_type: str,
    template_used: str,
    path: str,
    html_file: str,
    pdf_file: str,
    source_hash: str
) -> int:
    """
    Record a report file in the database.
    
    Args:
        conn: SQLite connection
        report_id: ID of the report run
        snapshot_table: Name of the snapshot table
        report_name: Name of the report
        report_type: Type of the report (summary, verify, etc.)
        template_used: Template file used
        path: Output folder path
        html_file: HTML output filename
        pdf_file: PDF output filename
        source_hash: Hash of the original source file
        
    Returns:
        ID of the inserted row
    """
    cursor = conn.cursor()
    
    cursor.execute(
        """
        INSERT INTO lookups_snapshot_reports 
        (report_id, snapshot_table, report_name, report_type, template_used, path, html_file, pdf_file, source_hash) 
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (report_id, snapshot_table, report_name, report_type, template_used, path, html_file, pdf_file, source_hash)
    )
    
    conn.commit()
    logger.info(f"Recorded report file {html_file} for report {report_id}")
    return cursor.lastrowid

def get_report_run(conn: sqlite3.Connection, report_id: str) -> Optional[Dict[str, Any]]:
    """
    Get a report run by its ID.
    
    Args:
        conn: SQLite connection
        report_id: ID of the report run
        
    Returns:
        Report run data as a dictionary, or None if not found
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM report_runs WHERE report_id = ?", (report_id,))
    row = cursor.fetchone()
    
    if not row:
        return None
    
    # Get column names
    column_names = [description[0] for description in cursor.description]
    
    # Create a dictionary of column names and values
    return dict(zip(column_names, row))

def get_report_files(conn: sqlite3.Connection, report_id: str) -> List[Dict[str, Any]]:
    """
    Get all report files for a report run.
    
    Args:
        conn: SQLite connection
        report_id: ID of the report run
        
    Returns:
        List of report file data as dictionaries
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM lookups_snapshot_reports WHERE report_id = ?", (report_id,))
    rows = cursor.fetchall()
    
    # Get column names
    column_names = [description[0] for description in cursor.description]
    
    # Create a list of dictionaries of column names and values
    return [dict(zip(column_names, row)) for row in rows]

def get_all_report_runs(conn: sqlite3.Connection) -> List[Dict[str, Any]]:
    """
    Get all report runs.
    
    Args:
        conn: SQLite connection
        
    Returns:
        List of report run data as dictionaries
    """
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM report_runs ORDER BY created_at DESC")
    rows = cursor.fetchall()
    
    # Get column names
    column_names = [description[0] for description in cursor.description]
    
    # Create a list of dictionaries of column names and values
    return [dict(zip(column_names, row)) for row in rows]

def check_report_freshness(
    conn: sqlite3.Connection, 
    report_id: str, 
    source_table_name: str
) -> Tuple[bool, Optional[str]]:
    """
    Check if a report is still fresh (based on table hash).
    
    Args:
        conn: SQLite connection
        report_id: ID of the report run
        source_table_name: Name of the source table to compare against
        
    Returns:
        Tuple of (is_fresh, current_hash)
        is_fresh: True if report is fresh, False otherwise
        current_hash: Current hash of the source table
    """
    # Get the report run
    report_run = get_report_run(conn, report_id)
    if not report_run:
        return False, None
    
    # Calculate the current hash of the source table
    current_hash = calculate_table_hash(conn, source_table_name)
    
    # Compare with the stored hash
    return report_run['table_hash'] == current_hash, current_hash
