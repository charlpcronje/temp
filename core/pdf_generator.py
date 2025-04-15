#!/usr/bin/env python
"""
PDF Generator - Generate PDF files from HTML files.
"""

import os
import json
import logging
import subprocess
import time
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
import re
from pathlib import Path # Added
import sys # Added

# Import multiprocessing conditionally
try:
    import multiprocessing
    MULTIPROCESSING_AVAILABLE = True
except ImportError:
    MULTIPROCESSING_AVAILABLE = False
    multiprocessing = None # Define it as None if not available

# Ensure core modules can be imported if run directly or imported
try:
    from core.session import get_current_session, get_session_dir, update_session_status, load_config
    from core.importer import get_table_data
    from core.logger import HTMLLogger
except ImportError:
    # Adjust path if running as a script might require this
    SCRIPT_DIR = Path(__file__).resolve().parent
    PROJECT_ROOT = SCRIPT_DIR.parent.parent
    sys.path.insert(0, str(PROJECT_ROOT))
    from core.session import get_current_session, get_session_dir, update_session_status, load_config
    from core.importer import get_table_data
    from core.logger import HTMLLogger

# Configure logging
logger = logging.getLogger(__name__)

# --- Worker Function (Top Level) ---
def _process_html_file_worker(
    html_file: str,
    html_dir: str,
    pdf_dir: str,
    pdf_method: str,
    config: Dict[str, Any] # Pass full config for generator functions
) -> Dict[str, Any]:
    """
    Worker function to convert a single HTML file to PDF.
    Moved outside generate_pdfs for multiprocessing compatibility.
    """
    html_path = os.path.join(html_dir, html_file)
    # Ensure pdf filename replaces .html (case-insensitive) and .htm
    pdf_base = re.sub(r'\.(html|htm)$', '', html_file, flags=re.IGNORECASE)
    pdf_file = f"{pdf_base}.pdf"
    pdf_path = os.path.join(pdf_dir, pdf_file)

    # Try to extract row number from filename (improved extraction)
    row_number = None
    # Matches _<digits>.<extension> at the end
    match = re.search(r'_(\d+)\.(html|htm)$', html_file, re.IGNORECASE)
    if match:
        try:
            row_number = int(match.group(1))
        except (ValueError, IndexError):
            logger.debug(f"Could not parse row number from suffix in {html_file}")
            pass
    # Fallback: try simple number before extension if no underscore match
    if row_number is None:
        # Matches <digits>.<extension> at the end
        match = re.search(r'(\d+)\.(html|htm)$', html_file, re.IGNORECASE)
        if match:
            try:
                # Avoid matching year/date as row number if filename has structure like YYYYMMDD_...
                if not re.match(r'^\d{8}_', html_file):
                     row_number = int(match.group(1))
                else:
                     logger.debug(f"Skipping potential row number match due to date-like prefix in {html_file}")
            except (ValueError, IndexError):
                 logger.debug(f"Could not parse row number from end of {html_file}")
                 pass

    if row_number is None:
         logger.warning(f"Could not determine row number from filename: {html_file}")


    start_time = time.time()

    try:
        logger.debug(f"Worker converting {html_file} to PDF using {pdf_method}...")

        if pdf_method == "weasyprint":
            result = generate_pdf_weasyprint(html_path, pdf_path, config)
        else: # Default to wkhtmltopdf
            result = generate_pdf_wkhtmltopdf(html_path, pdf_path, config)

        end_time = time.time()
        conversion_time = end_time - start_time

        # Return necessary info for DB insert later
        return {
            "html_file": html_file,
            "pdf_file": pdf_file,
            "success": result["success"],
            "error": result.get("error"),
            "conversion_time": conversion_time,
            "row_number": row_number # Include extracted row number (can be None)
        }

    except Exception as e:
        # Catch any unexpected error in the worker
        logger.error(f"Unexpected error in worker for {html_file}: {e}", exc_info=True)
        return {
            "html_file": html_file,
            "pdf_file": pdf_file,
            "success": False,
            "error": f"Worker unexpected error: {str(e)}",
            "conversion_time": time.time() - start_time,
            "row_number": row_number
        }
# === END WORKER FUNCTION ===

# --- Main PDF Generation Function ---
def generate_pdfs() -> Dict[str, Any]:
    """
    Generate PDF files from HTML files for the current session.
    Uses parallel processing for improved performance if available and beneficial.

    Returns:
        Dict containing generation results

    Raises:
        ValueError: If no active session found
        RuntimeError: If PDF generation fails
    """
    # Get current session
    session_hash = get_current_session()
    if not session_hash:
        raise ValueError("No active session found")

    logger.info(f"Starting PDF generation for session: {session_hash}")

    # Load config
    try:
        config = load_config()
    except Exception as e:
         logger.error(f"Failed to load configuration: {e}", exc_info=True)
         # Provide a minimal default config to attempt continuation
         config = {"pdf": {}}

    pdf_config = config.get("pdf", {})

    # Get paths
    try:
        session_dir = get_session_dir(session_hash)
        html_dir = os.path.join(session_dir, "html")
        pdf_dir = os.path.join(session_dir, "pdf")
    except ValueError as e:
         logger.error(f"Error getting session directory: {e}")
         raise RuntimeError(f"Cannot get session directory: {e}")

    # Ensure PDF directory exists
    try:
        os.makedirs(pdf_dir, exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create PDF directory {pdf_dir}: {e}")
        raise RuntimeError(f"Failed to create PDF directory: {e}")

    # --- Clear existing PDF files ---
    logger.info(f"Cleaning existing PDF files in {pdf_dir}")
    deleted_count = 0
    try:
        if os.path.exists(pdf_dir):
            for file in os.listdir(pdf_dir):
                if file.lower().endswith(".pdf"):
                    try:
                        os.remove(os.path.join(pdf_dir, file))
                        deleted_count += 1
                    except Exception as e:
                        logger.warning(f"Error removing existing PDF file {file}: {e}")
            logger.info(f"Removed {deleted_count} existing PDF files.")
        else:
             logger.warning(f"PDF directory did not exist for cleaning: {pdf_dir}")
    except OSError as e:
        logger.error(f"Error listing or cleaning PDF directory {pdf_dir}: {e}")
        # Decide if this is critical, maybe just log and continue

    # --- Find HTML files ---
    if not os.path.exists(html_dir):
        logger.error(f"HTML directory not found: {html_dir}")
        return {
            "num_files": 0, "pdf_files": [],
            "errors": [{"error": f"HTML directory not found: {html_dir}"}],
            "total_time": 0, "log_file": None
        }

    try:
        html_files = [f for f in os.listdir(html_dir) if f.lower().endswith((".html", ".htm"))]
    except OSError as e:
         logger.error(f"Error listing HTML files in {html_dir}: {e}")
         raise RuntimeError(f"Failed to list HTML files: {e}")


    if not html_files:
        logger.warning(f"No HTML files found in {html_dir}")
        return {
            "num_files": 0, "pdf_files": [], "errors": [],
             "total_time": 0, "log_file": None
        }

    logger.info(f"Found {len(html_files)} HTML files to convert to PDF")

    # --- Load session info (document type, input file) ---
    document_type = "unknown"
    input_file = ""
    try:
        # Find status.json relative to the project structure
        project_root_dir = Path(__file__).resolve().parent.parent.parent
        status_file_path = project_root_dir / "status.json"
        if status_file_path.exists():
            with open(status_file_path, 'r', encoding='utf-8') as f:
                status = json.load(f)
                # Verify hash matches current session if status file is shared
                if status.get("current_state", {}).get("hash") == session_hash:
                    document_type = status.get("current_state", {}).get("document_type", "unknown")
                    input_file = status.get("current_state", {}).get("imported_file", "")
                else:
                     logger.warning(f"Session hash in status.json does not match current session {session_hash}. Cannot determine document type.")
        else:
            logger.warning(f"status.json not found at {status_file_path}. Cannot determine document type.")
    except (json.JSONDecodeError, FileNotFoundError, OSError, TypeError) as e:
        logger.error(f"Error reading status.json: {e}")


    # --- Determine PDF method and prepare tasks ---
    pdf_method = pdf_config.get("generator", "wkhtmltopdf").lower()
    tasks = [
        (html_file, html_dir, pdf_dir, pdf_method, config) # Pass full config
        for html_file in html_files
    ]

    # --- Execute Tasks (Parallel or Sequential) ---
    results = []
    multiprocessing_threshold = pdf_config.get("multiprocessing_threshold", 50)
    multiprocessing_workers = pdf_config.get("multiprocessing_workers", 4)

    use_multiprocessing = (
        MULTIPROCESSING_AVAILABLE and
        len(html_files) > multiprocessing_threshold and
        pdf_method == "wkhtmltopdf" # Often WeasyPrint doesn't benefit as much or has issues
    )

    start_pool_time = time.time()
    if use_multiprocessing:
        num_workers = min(multiprocessing.cpu_count(), multiprocessing_workers)
        logger.info(f"Using multiprocessing with {num_workers} workers (threshold: {multiprocessing_threshold})...")
        try:
            # Ensure the worker function is picklable (defined at top level)
            if multiprocessing: # Check again as it's defined as None if import fails
                with multiprocessing.Pool(processes=num_workers) as pool:
                    results = pool.starmap(_process_html_file_worker, tasks)
            else:
                 raise RuntimeError("Multiprocessing module was not imported correctly.") # Should not happen if check passed
        except Exception as mp_err:
             logger.error(f"Multiprocessing pool failed: {mp_err}. Falling back to sequential processing.", exc_info=True)
             use_multiprocessing = False # Ensure sequential fallback runs
             results = [] # Reset results
    else:
        logger.info("Processing sequentially (multiprocessing disabled, not available, threshold not met, or method unsuitable)...")

    # Run sequentially if multiprocessing was disabled or failed
    if not use_multiprocessing:
        # Call the top-level worker function correctly
        results = [_process_html_file_worker(*task_args) for task_args in tasks]

    end_pool_time = time.time()
    logger.info(f"PDF conversion process took {end_pool_time - start_pool_time:.2f} seconds.")


    # --- Process results and handle DB inserts in the main thread ---
    pdf_files = []
    errors = []
    conversion_times = []
    db_conn = None
    generated_table_name = None

    try:
        # Initialize database connection
        db_path = os.path.join(session_dir, "data.db")
        db_conn = sqlite3.connect(db_path, timeout=10) # Add timeout
        cursor = db_conn.cursor()

        # Get the table hash and check table existence
        try:
            table_hash, _, _ = get_table_data(session_hash) # Requires DB access
            generated_table_name = f"generated_{table_hash}"
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{generated_table_name}'")
            table_exists = cursor.fetchone() is not None
            if not table_exists:
                logger.warning(f"Table {generated_table_name} not found. PDF metadata won't be saved.")
                generated_table_name = None
        except Exception as db_err:
             logger.error(f"Could not get table hash or check table existence: {db_err}. PDF metadata won't be saved.")
             generated_table_name = None

        # Process results from workers
        for result in results:
            if result["success"]:
                pdf_files.append(result["pdf_file"])
                conversion_times.append(result["conversion_time"])
                logger.debug(f"Successfully generated PDF: {result['pdf_file']} in {result['conversion_time']:.2f} seconds")

                # Save PDF metadata to database if table exists
                if generated_table_name:
                    try:
                        db_data = {"file": result["html_file"], "converted_to": result["pdf_file"]}
                        row_num_to_insert = result.get("row_number") # Can be None
                        # Handle None row_number - decide on a convention (e.g., 0 or -1, or NULL if DB allows)
                        if row_num_to_insert is None:
                             row_num_to_insert = 0 # Or handle as NULL if schema allows

                        cursor.execute(
                            f"INSERT INTO {generated_table_name} (document_type, mime_type, input_file, row, data) VALUES (?, ?, ?, ?, ?)",
                            (
                                document_type,
                                "application/pdf",
                                input_file,
                                row_num_to_insert,
                                json.dumps(db_data)
                            )
                        )
                        # Commit frequently or at the end? For robustness, maybe commit in batches or at end.
                        # db_conn.commit() # Commit per insert can be slow
                    except sqlite3.Error as e:
                        logger.error(f"Error logging PDF generation to database for {result['pdf_file']}: {e}")
                        # Decide whether to rollback or just log
                        # db_conn.rollback()
            else:
                errors.append({
                    "file": result["html_file"],
                    "error": result["error"]
                })
                logger.error(f"Failed to generate PDF for {result['html_file']}: {result['error']}")

        # Commit all successful DB inserts at the end
        if generated_table_name:
            try:
                db_conn.commit()
                logger.info("Committed PDF metadata inserts to database.")
            except sqlite3.Error as e:
                 logger.error(f"Failed to commit PDF metadata to database: {e}")


    except sqlite3.Error as e:
        logger.error(f"Database connection or operation error: {e}", exc_info=True)
        # Add error to list? Maybe a general DB error.
        errors.append({"file": "Database", "error": f"DB Error: {e}"})
    except Exception as e:
         logger.error(f"Unexpected error during result processing: {e}", exc_info=True)
         errors.append({"file": "Processing", "error": f"General Error: {e}"})
    finally:
        # Ensure database connection is closed
        if db_conn:
            db_conn.close()
            logger.debug("Database connection closed.")


    # --- Final Steps ---
    # Update session status
    try:
        update_session_status(
            session_hash,
            file_path=input_file, # Pass input_file again
            operation="GENERATE_PDF"
        )
    except Exception as e:
        logger.error(f"Failed to update session status after PDF generation: {e}")


    # Log PDF generation summary
    log_file = None
    try:
        html_logger = HTMLLogger(session_hash)
        log_file = html_logger.log_pdf_generation(
            num_files=len(pdf_files),
            conversion_times=conversion_times,
            file_list=pdf_files,
            errors=errors
        )
    except Exception as e:
         logger.error(f"Failed to generate PDF summary log: {e}")

    # Optionally generate execution summary and dashboard
    if pdf_config.get("generate_summary_logs", True): # Make this configurable
        try:
            html_logger = HTMLLogger(session_hash) # Re-initialize if needed
            html_logger.generate_execution_summary(
                steps_completed=["import", "validate", "map", "html", "pdf"],
                stats={
                    "num_html_files": len(html_files),
                    "num_pdf_files": len(pdf_files),
                    "total_conversion_time": sum(conversion_times),
                    "avg_conversion_time": sum(conversion_times) / len(conversion_times) if conversion_times else 0,
                    "errors": len(errors)
                }
            )
            html_logger.generate_dashboard()
        except Exception as log_err:
            logger.error(f"Failed to generate final summary/dashboard logs: {log_err}")


    logger.info(f"PDF generation complete for session {session_hash}. Success: {len(pdf_files)}, Errors: {len(errors)}.")

    return {
        "num_files": len(pdf_files),
        "pdf_files": pdf_files,
        "total_time": sum(conversion_times),
        "errors": errors,
        "log_file": log_file # Path to the summary log file
    }

def generate_pdf_wkhtmltopdf(html_path: str, pdf_path: str,
                           config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a PDF using wkhtmltopdf.
    """
    pdf_config = config.get("pdf", {})
    # --- CORRECTED KEY HERE ---
    # Ensure 'wkhtmltopdf' is in PATH or provide full path in config
    wkhtmltopdf_path = pdf_config.get("wkhtmltopdf", "wkhtmltopdf")
    # --- END CORRECTION ---

    # Default margins (can be overridden by schema or config)
    # Uses the 'margin' key from dev.json as the base default
    default_margin = pdf_config.get("margin", "10mm")
    margins = {
        # These specific margin keys are not in dev.json, so they will use default_margin
        "top": pdf_config.get("margin_top", default_margin),
        "bottom": pdf_config.get("margin_bottom", default_margin),
        "left": pdf_config.get("margin_left", default_margin),
        "right": pdf_config.get("margin_right", default_margin)
    }

    # Try to get document type and load schema margins
    document_type = None
    schema_margins_found = False # Flag to track if we successfully found schema margins
    try:
        # Find status.json relative to the project structure
        project_root_dir = Path(__file__).resolve().parent.parent
        status_file_path = project_root_dir / "status.json"

        if status_file_path.exists():
            with open(status_file_path, 'r', encoding='utf-8') as f:
                status = json.load(f)
                document_type = status.get("current_state", {}).get("document_type")
        else:
            logger.warning(f"status.json not found at {status_file_path}, cannot determine document type for schema margins.")

        if document_type:
            schema_dir = project_root_dir / "schemas"
            if schema_dir.is_dir():
                schema_found = False
                for schema_file_path in schema_dir.glob('*.json'):
                    try:
                        with open(schema_file_path, 'r', encoding='utf-8') as sf:
                            schema_content = json.load(sf)
                            # Check if this is the correct schema based on type
                            if schema_content.get("type") == document_type:
                                schema_found = True
                                logger.debug(f"Found matching schema: {schema_file_path.name}")
                                # Check for layout and margins within the loaded schema content
                                if "layout" in schema_content:
                                    schema_layout = schema_content.get("layout", {})
                                    specific_margins = schema_layout.get("margins", {})
                                    if specific_margins: # Check if the margins dict is not empty
                                        logger.info(f"Applying margins from schema '{schema_file_path.name}': {specific_margins}")
                                        margins.update(specific_margins) # Update defaults with schema values
                                        schema_margins_found = True
                                    else:
                                         logger.debug(f"Schema '{schema_file_path.name}' has 'layout' but no 'margins' defined.")
                                else:
                                    logger.debug(f"Schema '{schema_file_path.name}' does not have a 'layout' section.")
                                # Stop searching once the correct schema is found and processed
                                break
                    except json.JSONDecodeError as json_err:
                         logger.warning(f"Error decoding JSON from schema file {schema_file_path.name}: {json_err}")
                    except Exception as read_err:
                         logger.warning(f"Error reading schema file {schema_file_path.name}: {read_err}")
                if not schema_found:
                     logger.warning(f"No schema file found with type '{document_type}' in {schema_dir}.")
            else:
                 logger.warning(f"Schemas directory not found: {schema_dir}")
        else:
             logger.info("Document type not determined from status.json, using default margins.")

    except Exception as e:
         logger.warning(f"Could not load document type or schema information for margins due to error: {e}", exc_info=True)

    # Log final margins being used
    if not schema_margins_found:
         logger.info(f"Using default/config margins: {margins}")

    # Build command
    cmd = [
        wkhtmltopdf_path,
        "--enable-local-file-access",
        "--load-error-handling", "ignore",
        "--load-media-error-handling", "ignore",
        "--quiet",
        # Uses 'page_size' and 'orientation' from dev.json
        "--page-size", pdf_config.get("page_size", "A4"),
        "--orientation", pdf_config.get("orientation", "Portrait"),
        # Uses margins derived above
        "--margin-top", margins.get("top", "10mm"),
        "--margin-bottom", margins.get("bottom", "10mm"),
        "--margin-left", margins.get("left", "10mm"),
        "--margin-right", margins.get("right", "10mm"),
    ]
    # 'wkhtmltopdf_options' is not in dev.json, default [] will be used
    extra_options = pdf_config.get("wkhtmltopdf_options", [])
    if isinstance(extra_options, list):
        cmd.extend(extra_options)
    else:
        logger.warning(f"wkhtmltopdf_options in config is not a list: {extra_options}")

    cmd.extend([str(html_path), str(pdf_path)])

    logger.debug(f"Running wkhtmltopdf command: {' '.join(cmd)}")

    try:
        # 'timeout' is not in dev.json, default 60 will be used
        process = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
            timeout=pdf_config.get("timeout", 60)
        )

        if process.returncode != 0 and process.returncode != 1:
            error_detail = process.stderr or process.stdout or f"Unknown wkhtmltopdf error (code {process.returncode})"
            logger.error(f"wkhtmltopdf failed for {html_path} (code {process.returncode}): {error_detail}")
            return {"success": False, "error": f"wkhtmltopdf error (code {process.returncode}): {error_detail[:500]}"}

        error_patterns = ["error:", "failed", "could not load", "segmentation fault", "crash"]
        stderr_lower = process.stderr.lower()
        if any(pattern in stderr_lower for pattern in error_patterns):
             logger.error(f"wkhtmltopdf reported potential errors for {html_path}: {process.stderr}")

        if not os.path.exists(pdf_path) or os.path.getsize(pdf_path) < 100:
            error_msg = f"wkhtmltopdf ran but PDF file not created or is too small (<100 bytes): {pdf_path}"
            logger.error(error_msg)
            if process.stderr:
                 error_msg += f"\nstderr: {process.stderr[:500]}"
            return {"success": False, "error": error_msg}

        if process.returncode == 1:
            logger.warning(f"wkhtmltopdf completed with warnings for {html_path}. PDF generated. stderr: {process.stderr[:500]}")
            return {"success": True, "warning": process.stderr[:500]}

        return {"success": True}

    except FileNotFoundError:
         error_msg = f"wkhtmltopdf executable not found at '{wkhtmltopdf_path}'. Please ensure it's installed and in your PATH or provide the full path in config ('pdf.wkhtmltopdf')."
         logger.error(error_msg)
         return {"success": False, "error": error_msg}
    except subprocess.TimeoutExpired:
        error_msg = f"wkhtmltopdf timed out after {pdf_config.get('timeout', 60)} seconds for {html_path}."
        logger.error(error_msg)
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"Unexpected error generating PDF with wkhtmltopdf: {str(e)}"
        logger.error(error_msg, exc_info=True)
        return {"success": False, "error": error_msg}


def generate_pdf_weasyprint(html_path: str, pdf_path: str,
                          config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate a PDF using WeasyPrint.
    """
    pdf_config = config.get("pdf", {})
    try:
        try:
            from weasyprint import HTML, CSS
            from weasyprint.fonts import FontConfiguration
        except ImportError:
            error_msg = "WeasyPrint not installed. Install with: pip install weasyprint"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

        font_config = FontConfiguration()
        css_list = []
        # Use CSS files specified in config
        css_files_config = pdf_config.get("weasyprint_css_files", [])

        # Look for default CSS in standard locations if needed
        default_css_paths = [
            Path(html_path).parent / "style.css", # CSS in same folder as HTML
             # CSS in www/assets relative to session
            Path(html_path).parent.parent / "www" / "assets" / "style.css",
        ]
        css_to_use = set() # Avoid duplicates

        # Add configured CSS files first
        if isinstance(css_files_config, list):
            for css_file in css_files_config:
                css_path = Path(css_file)
                if css_path.exists():
                    css_to_use.add(css_path)
                else:
                    logger.warning(f"Configured Weasyprint CSS file not found: {css_file}")
        else:
            logger.warning(f"Config key 'pdf.weasyprint_css_files' is not a list.")

        # Check default locations if no specific CSS is configured
        if not css_to_use:
             for p in default_css_paths:
                  if p.exists():
                       css_to_use.add(p)
                       logger.info(f"Using default CSS for Weasyprint: {p}")
                       break # Usually only one default style is needed

        # Create CSS objects
        for css_path in css_to_use:
             try:
                  css_list.append(CSS(filename=str(css_path), font_config=font_config))
             except Exception as css_err:
                  logger.error(f"Error loading Weasyprint CSS file {css_path}: {css_err}")


        # Set base_url to the HTML directory for relative paths (images, etc.)
        base_url = Path(html_path).parent.as_uri() # Use file URI scheme

        # Render PDF
        HTML(filename=str(html_path), base_url=base_url).write_pdf(
            str(pdf_path),
            stylesheets=css_list if css_list else None,
            font_config=font_config,
            # Add optimization options if needed (can increase memory usage)
            # optimize_images=True,
            # optimize_size=('fonts', 'images', 'all')
        )

        # Verify PDF was created and not empty
        if not os.path.exists(pdf_path) or os.path.getsize(pdf_path) < 100: # Size threshold
            error_msg = "WeasyPrint ran but PDF file not created or is too small (<100 bytes)"
            logger.error(error_msg)
            return {"success": False, "error": error_msg}

        return {"success": True}

    except Exception as e:
        error_msg = f"Error generating PDF with WeasyPrint: {str(e)}"
        logger.error(error_msg, exc_info=True) # Log full traceback
        return {"success": False, "error": error_msg}