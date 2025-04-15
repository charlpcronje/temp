#!/usr/bin/env python
"""
Reporter Module - Handles the generation of report templates and files.
"""

import os
import json
import logging
import shutil
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import jinja2

from core.session import get_current_session, get_session_dir, update_session_status
from core.report_db import (
    init_reporting_db,
    generate_snapshot_table,
    calculate_table_hash,
    generate_report_id,
    report_table_exists,
    record_report_run,
    record_report_file,
    get_report_run,
    get_report_files,
    check_report_freshness
)

# Configure logging
logger = logging.getLogger(__name__)

# Report types
REPORT_TYPES = {
    "summary": {
        "name": "Session Summary",
        "template": "summary.jinja2",
        "description": "Overall session status and document type"
    },
    "mapping": {
        "name": "Field Mappings",
        "template": "mapping.jinja2",
        "description": "Field mappings, inference results, unmatched columns"
    },
    "verify": {
        "name": "Lookup Verification",
        "template": "verify.jinja2",
        "description": "Lookup matches and user binding status"
    },
    "exceptions": {
        "name": "Exceptions",
        "template": "exceptions.jinja2",
        "description": "All unresolved lookups and data issues"
    }
}

def render_report(
    template_name: str, 
    data: Dict[str, Any], 
    output_path: str
) -> str:
    """
    Render a report template with the provided data.
    
    Args:
        template_name: Name of the template file
        data: Data to render into the template
        output_path: Path to write the rendered HTML
        
    Returns:
        Path to the rendered HTML file
    """
    # Get the templates directory
    templates_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "reports")
    
    # Create Jinja2 environment
    env = jinja2.Environment(
        loader=jinja2.FileSystemLoader(templates_dir),
        autoescape=jinja2.select_autoescape(['html', 'xml'])
    )
    
    try:
        # Load and render the template
        template = env.get_template(template_name)
        rendered_html = template.render(**data)
        
        # Write the rendered HTML to the output file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(rendered_html)
        
        logger.info(f"Rendered report template {template_name} to {output_path}")
        return output_path
    
    except jinja2.exceptions.TemplateNotFound:
        logger.error(f"Template {template_name} not found in {templates_dir}")
        raise FileNotFoundError(f"Template {template_name} not found")
    
    except Exception as e:
        logger.error(f"Error rendering template {template_name}: {e}")
        raise

def convert_html_to_pdf(html_path: str) -> str:
    """
    Convert an HTML file to PDF.
    
    Args:
        html_path: Path to the HTML file
        
    Returns:
        Path to the generated PDF file
    """
    # Determine the output PDF path (same location but with .pdf extension)
    pdf_path = os.path.splitext(html_path)[0] + ".pdf"
    
    try:
        # Import weasyprint locally to avoid global import issues
        from weasyprint import HTML, CSS
        
        # Get the directory of the HTML file for base_url
        base_url = os.path.dirname(html_path)
        
        # Convert HTML to PDF
        html = HTML(filename=html_path, base_url=base_url)
        
        # Get the CSS file
        css_path = os.path.join(base_url, "style.css")
        css = None
        if os.path.exists(css_path):
            css = CSS(filename=css_path)
            logger.info(f"Using CSS from {css_path}")
        
        # Generate PDF
        html.write_pdf(pdf_path, stylesheets=[css] if css else None)
        logger.info(f"Converted {html_path} to {pdf_path}")
        
        return pdf_path
    
    except ImportError:
        logger.error("WeasyPrint not installed. Please install with 'pip install weasyprint'")
        raise
    
    except Exception as e:
        logger.error(f"Error converting {html_path} to PDF: {e}")
        raise

def copy_style(target_folder: str) -> str:
    """
    Copy the style.css file to the output folder.
    
    Args:
        target_folder: Path to the target folder
        
    Returns:
        Path to the copied CSS file
    """
    # Get the styles directory
    styles_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates", "styles")
    source_css = os.path.join(styles_dir, "style.css")
    
    # Check if a tenant-specific style exists
    # TODO: Implement tenant-specific styling
    
    # Ensure the source CSS exists
    if not os.path.exists(source_css):
        logger.error(f"Source CSS file {source_css} not found")
        raise FileNotFoundError(f"Source CSS file {source_css} not found")
    
    # Ensure the target folder exists
    os.makedirs(target_folder, exist_ok=True)
    
    # Copy the CSS file
    target_css = os.path.join(target_folder, "style.css")
    shutil.copy(source_css, target_css)
    
    logger.info(f"Copied style.css to {target_css}")
    return target_css

def generate_meta_json(
    conn: sqlite3.Connection,
    report_id: str,
    output_folder: str
) -> str:
    """
    Generate a meta.json file with information about all reports in a batch.
    
    Args:
        conn: SQLite connection
        report_id: ID of the report run
        output_folder: Path to the output folder
        
    Returns:
        Path to the generated meta.json file
    """
    # Get the report run data
    report_run = get_report_run(conn, report_id)
    if not report_run:
        raise ValueError(f"Report run {report_id} not found")
    
    # Get all report files
    report_files = get_report_files(conn, report_id)
    
    # Create the meta.json data
    meta_data = {
        "report_id": report_id,
        "created_at": report_run["created_at"],
        "snapshot_table": report_run["snapshot_table"],
        "source_hash": report_run["session_hash"],
        "reports": [
            {
                "name": r["report_name"],
                "type": r["report_type"],
                "template": r["template_used"],
                "html_file": r["html_file"],
                "pdf_file": r["pdf_file"]
            }
            for r in report_files
        ]
    }
    
    # Write the meta.json file
    meta_path = os.path.join(output_folder, "meta.json")
    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta_data, f, indent=2)
    
    logger.info(f"Generated meta.json at {meta_path}")
    return meta_path

def create_report_directories(session_hash: str, table_hash: str) -> str:
    """
    Create the directory structure for reports.
    
    Args:
        session_hash: Hash of the session
        table_hash: Hash of the source table
        
    Returns:
        Path to the reports directory
    """
    # Get the session directory
    session_dir = get_session_dir(session_hash)
    
    # Create the reports directory
    reports_dir = os.path.join(session_dir, "reports", f"hash{table_hash}")
    os.makedirs(reports_dir, exist_ok=True)
    
    logger.info(f"Created reports directory at {reports_dir}")
    return reports_dir

def generate_all_reports(session_hash: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate all reports for a session.
    
    Args:
        session_hash: Hash of the session, or None to use current session
        
    Returns:
        Dictionary with report generation results
    """
    # Get the current session if not provided
    if not session_hash:
        session_hash = get_current_session()
        if not session_hash:
            raise ValueError("No active session found. Please import a file first.")
    
    # Initialize the reporting database
    conn = init_reporting_db(session_hash)
    
    # Create a snapshot of the current data table
    source_table_name = f"generated_{session_hash}"
    snapshot_table_name, table_hash = generate_snapshot_table(conn, source_table_name)
    
    # Generate a report ID
    report_id = generate_report_id()
    
    # Get the source file from the current session
    session_dir = get_session_dir(session_hash)
    status_path = os.path.join(os.path.dirname(session_dir), "status.json")
    with open(status_path, 'r') as f:
        status = json.load(f)
    source_file = status.get("current_state", {}).get("imported_file", "unknown")
    
    # Record the report run
    record_report_run(conn, report_id, session_hash, snapshot_table_name, table_hash, source_file)
    
    # Create the reports directory
    reports_dir = create_report_directories(session_hash, table_hash)
    
    # Copy the style.css file
    copy_style(reports_dir)
    
    # Collect data for reports
    report_data = collect_report_data(conn, session_hash, snapshot_table_name)
    
    # Generate each report type
    generated_reports = []
    for report_type, report_info in REPORT_TYPES.items():
        try:
            # Render the HTML report
            html_filename = f"{report_type}.html"
            html_path = os.path.join(reports_dir, html_filename)
            render_report(report_info["template"], report_data, html_path)
            
            # Convert to PDF
            pdf_filename = f"{report_type}.pdf"
            pdf_path = convert_html_to_pdf(html_path)
            
            # Record the report file
            record_report_file(
                conn,
                report_id,
                snapshot_table_name,
                report_info["name"],
                report_type,
                report_info["template"],
                reports_dir,
                html_filename,
                pdf_filename,
                session_hash
            )
            
            generated_reports.append({
                "type": report_type,
                "html_path": html_path,
                "pdf_path": pdf_path
            })
            
        except Exception as e:
            logger.error(f"Error generating {report_type} report: {e}")
            # Continue with other reports even if one fails
    
    # Generate meta.json
    meta_path = generate_meta_json(conn, report_id, reports_dir)
    
    # Generate index.html if needed
    index_html = generate_index_html(conn, report_id, reports_dir, report_data)
    
    # Update session status
    update_session_status(session_hash, operation="REPORT_GENERATED")
    
    # Return results
    results = {
        "report_id": report_id,
        "reports_directory": reports_dir,
        "generated_reports": generated_reports,
        "meta_json": meta_path,
        "index_html": index_html,
        "snapshot_table": snapshot_table_name
    }
    
    logger.info(f"Generated all reports with ID {report_id} for session {session_hash}")
    return results

def collect_report_data(
    conn: sqlite3.Connection,
    session_hash: str,
    snapshot_table: str
) -> Dict[str, Any]:
    """
    Collect data for report generation.
    
    Args:
        conn: SQLite connection
        session_hash: Hash of the session
        snapshot_table: Name of the snapshot table
        
    Returns:
        Dictionary with data for report templates
    """
    # Get session data
    session_dir = get_session_dir(session_hash)
    status_path = os.path.join(os.path.dirname(session_dir), "status.json")
    with open(status_path, 'r') as f:
        status = json.load(f)
    
    # Load mapping.json if it exists
    mapping_path = os.path.join(session_dir, "mappings", "mapping.json")
    mapping_data = {}
    if os.path.exists(mapping_path):
        with open(mapping_path, 'r') as f:
            mapping_data = json.load(f)
    
    # Get data from the snapshot table
    cursor = conn.cursor()
    cursor.execute(f"SELECT COUNT(*) FROM {snapshot_table}")
    total_rows = cursor.fetchone()[0]
    
    # Get column information
    cursor.execute(f"PRAGMA table_info({snapshot_table})")
    columns = [col[1] for col in cursor.fetchall()]
    
    # Get lookup information if available
    lookup_data = {}
    lookup_path = os.path.join(session_dir, "mappings", "lookups.json")
    if os.path.exists(lookup_path):
        with open(lookup_path, 'r') as f:
            lookup_data = json.load(f)
    
    # Get generated files information
    html_dir = os.path.join(session_dir, "html")
    pdf_dir = os.path.join(session_dir, "pdf")
    html_files = []
    pdf_files = []
    if os.path.exists(html_dir):
        html_files = [f for f in os.listdir(html_dir) if f.endswith(".html")]
    if os.path.exists(pdf_dir):
        pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
    
    # Compile all data
    report_data = {
        "session": {
            "hash": session_hash,
            "imported_file": status.get("current_state", {}).get("imported_file", "unknown"),
            "imported_on": status.get("current_state", {}).get("last_updated", "unknown"),
            "document_type": status.get("current_state", {}).get("document_type", "unknown"),
            "output_folder": session_dir,
            "sqlite_db": status.get("current_state", {}).get("sqlite_db_file", "unknown")
        },
        "dataset": {
            "total_rows": total_rows,
            "columns": columns,
            "mapping": mapping_data
        },
        "documents": {
            "html_files": html_files,
            "pdf_files": pdf_files,
            "html_count": len(html_files),
            "pdf_count": len(pdf_files)
        },
        "lookups": lookup_data,
        "exceptions": extract_exceptions(conn, snapshot_table, lookup_data),
        "report_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return report_data

def extract_exceptions(
    conn: sqlite3.Connection, 
    snapshot_table: str, 
    lookup_data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Extract exceptions from the snapshot table.
    
    Args:
        conn: SQLite connection
        snapshot_table: Name of the snapshot table
        lookup_data: Lookup data from lookups.json
        
    Returns:
        Dictionary with exception data
    """
    # Initialize exceptions dictionary
    exceptions = {
        "unmatched_rows": [],
        "ambiguous_matches": [],
        "missing_fields": [],
        "validation_errors": []
    }
    
    # Find unmatched rows based on lookup_data
    # This is simplified and would need to be adapted to your specific data structure
    if "matches" in lookup_data:
        for row_id, match_data in lookup_data.get("matches", {}).items():
            if not match_data.get("matched_user_id"):
                # Get row data
                cursor = conn.cursor()
                cursor.execute(f"SELECT * FROM {snapshot_table} WHERE rowid = ?", (row_id,))
                row = cursor.fetchone()
                if row:
                    # Get column names
                    cursor.execute(f"PRAGMA table_info({snapshot_table})")
                    columns = [col[1] for col in cursor.fetchall()]
                    row_dict = dict(zip(columns, row))
                    
                    exceptions["unmatched_rows"].append({
                        "row_id": row_id,
                        "data": row_dict,
                        "reason": match_data.get("reason", "Unknown")
                    })
            elif match_data.get("ambiguous", False):
                exceptions["ambiguous_matches"].append({
                    "row_id": row_id,
                    "possible_matches": match_data.get("possible_matches", []),
                    "reason": match_data.get("reason", "Multiple matches found")
                })
    
    # Add any validation errors from the validation phase
    # This would need to be adapted to your validation data structure
    
    return exceptions

def generate_index_html(
    conn: sqlite3.Connection,
    report_id: str,
    reports_dir: str,
    report_data: Dict[str, Any]
) -> str:
    """
    Generate an index.html file that links to all reports.
    
    Args:
        conn: SQLite connection
        report_id: ID of the report run
        reports_dir: Path to the reports directory
        report_data: Data used for report generation
        
    Returns:
        Path to the index.html file
    """
    # Get the report files
    report_files = get_report_files(conn, report_id)
    
    # Create index data
    index_data = {
        "report_id": report_id,
        "report_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "session": report_data["session"],
        "reports": [
            {
                "name": r["report_name"],
                "type": r["report_type"],
                "description": REPORT_TYPES.get(r["report_type"], {}).get("description", ""),
                "html_file": r["html_file"],
                "pdf_file": r["pdf_file"]
            }
            for r in report_files
        ]
    }
    
    # Render the index.html
    index_path = os.path.join(reports_dir, "index.html")
    render_report("index.jinja2", index_data, index_path)
    
    # Copy the index.html to www folder as well for easy access
    session_dir = get_session_dir(report_data["session"]["hash"])
    www_dir = os.path.join(session_dir, "www")
    shutil.copy(index_path, os.path.join(www_dir, "reports.html"))
    
    return index_path

def rerun_report(report_id: str) -> Dict[str, Any]:
    """
    Re-run a previously generated report.
    
    Args:
        report_id: ID of the report to re-run
        
    Returns:
        Dictionary with report generation results
    """
    # Initialize the reporting database using the system-wide session
    session_hash = get_current_session()
    if not session_hash:
        raise ValueError("No active session found. Please import a file first.")
    
    conn = init_reporting_db(session_hash)
    
    # Get the report run
    report_run = get_report_run(conn, report_id)
    if not report_run:
        raise ValueError(f"Report run {report_id} not found")
    
    # Get the source table name
    source_table_name = f"generated_{report_run['session_hash']}"
    
    # Check if the report is still fresh
    is_fresh, current_hash = check_report_freshness(conn, report_id, source_table_name)
    
    if is_fresh:
        logger.info(f"Report {report_id} is still fresh, no need to regenerate")
        return {
            "report_id": report_id,
            "status": "fresh",
            "message": "Reports are still valid, no regeneration needed"
        }
    
    # If not fresh, generate new reports
    logger.info(f"Report {report_id} is stale, regenerating with new data")
    return generate_all_reports(report_run['session_hash'])

def list_reports() -> List[Dict[str, Any]]:
    """
    List all report runs.
    
    Returns:
        List of report run data as dictionaries
    """
    # Initialize the reporting database using the system-wide session
    session_hash = get_current_session()
    if not session_hash:
        raise ValueError("No active session found. Please import a file first.")
    
    conn = init_reporting_db(session_hash)
    
    # Get all report runs
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            r.report_id, 
            r.session_hash, 
            r.snapshot_table, 
            r.table_hash, 
            r.created_at,
            COUNT(DISTINCT f.report_type) as report_count,
            MAX(f.created_at) as last_updated
        FROM 
            report_runs r
        LEFT JOIN 
            lookups_snapshot_reports f ON r.report_id = f.report_id
        GROUP BY 
            r.report_id
        ORDER BY 
            r.created_at DESC
    """)
    rows = cursor.fetchall()
    
    # Get column names
    column_names = [description[0] for description in cursor.description]
    
    # Create a list of dictionaries
    reports = []
    source_table_name = f"generated_{session_hash}"
    
    for row in rows:
        report_dict = dict(zip(column_names, row))
        
        # Check if the report is still fresh
        try:
            is_fresh, _ = check_report_freshness(conn, report_dict["report_id"], source_table_name)
            report_dict["is_fresh"] = is_fresh
        except Exception:
            report_dict["is_fresh"] = False
        
        reports.append(report_dict)
    
    return reports
