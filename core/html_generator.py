#!/usr/bin/env python
"""
HTML Generator - Generate HTML files from templates and data.
"""
import base64
from pathlib import Path
import os
import json
import logging
import sqlite3
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import re

import jinja2

from core.session import get_current_session, get_session_dir, update_session_status
from core.importer import get_table_data
from core.mapper import load_mapping
from core.logger import HTMLLogger

# Configure logging
logger = logging.getLogger(__name__)

# Set up Jinja2 environment for document templates
template_loader = jinja2.FileSystemLoader(searchpath="templates/html")
jinja_env = jinja2.Environment(loader=template_loader)


def get_image_as_base64(image_path: str) -> str:
    """
    Convert an image file to a base64 encoded string.

    Args:
        image_path: Path to the image file

    Returns:
        Base64 encoded string of the image
    """
    try:
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

        # Determine MIME type based on file extension
        ext = Path(image_path).suffix.lower()
        mime_type = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.gif': 'image/gif',
            '.svg': 'image/svg+xml',
            '.webp': 'image/webp'
        }.get(ext, 'application/octet-stream')

        return f"data:{mime_type};base64,{encoded_string}"
    except Exception as e:
        logger.warning(f"Error encoding image {image_path} to base64: {e}")
        return ""

def generate_html_files() -> Dict[str, Any]:
    """
    Generate HTML files from the current session data and mapping.
    Handles duplicate filenames by appending sequence numbers.

    Returns:
        Dict containing generation results

    Raises:
        ValueError: If session, document type, or mapping not found
        TemplateError: If template loading or rendering fails
    """
    # Get current session
    session_hash = get_current_session()
    if not session_hash:
        raise ValueError("No active session found")

    session_dir = get_session_dir(session_hash)

    # Load document type from status.json
    document_type = None
    input_file = ""
    schema_for_doc = None # Store the matched schema
    try:
        # Find status.json relative to the project structure
        project_root_dir = Path(__file__).resolve().parent.parent
        status_file_path = project_root_dir / "status.json"

        if not status_file_path.exists():
            raise FileNotFoundError(f"status.json not found at {status_file_path}")

        with open(status_file_path, 'r', encoding='utf-8') as f:
            status = json.load(f)
            current_state = status.get("current_state", {})
            # Ensure hash matches current session
            if current_state.get("hash") != session_hash:
                 logger.warning(f"Session hash in status.json ({current_state.get('hash')}) does not match current session ({session_hash}).")
                 # Decide how to handle this - maybe raise error or just use current session hash
                 # For now, we proceed but document type might be wrong if status is stale
            document_type = current_state.get("document_type")
            input_file = current_state.get("imported_file", "") # Get input file here
    except (json.JSONDecodeError, FileNotFoundError, OSError, TypeError) as e:
        logger.error(f"Error reading status.json: {e}", exc_info=True)
        raise ValueError("Could not read document type or input file from status.json")

    if not document_type:
        raise ValueError("Document type not found or is null in status.json")
    if not input_file:
        logger.warning("Imported file path not found in status.json. Logging may be incomplete.")


    # Get field mapping
    field_mapping = load_mapping(session_hash)
    if not field_mapping:
        # Try generating mapping if not found
        try:
            logger.info("Mapping file not found, attempting to generate mapping...")
            from .mapper import generate_mapping_file # Local import
            generate_mapping_file()
            field_mapping = load_mapping(session_hash)
            if not field_mapping:
                 raise ValueError("No field mapping found. Run mapper first.")
        except Exception as map_err:
             logger.error(f"Failed to generate mapping: {map_err}", exc_info=True)
             raise ValueError("No field mapping found. Run mapper first.")


    # Get schemas to find template name and the specific schema object
    schemas_dir = "schemas"
    template_name = None
    try:
        project_root_dir = Path(__file__).resolve().parent.parent
        schema_dir_path = project_root_dir / schemas_dir
        if not schema_dir_path.is_dir():
            raise FileNotFoundError(f"Schemas directory not found at {schema_dir_path}")

        for filename in os.listdir(schema_dir_path):
            if filename.lower().endswith(".json"):
                try:
                    with open(schema_dir_path / filename, 'r', encoding='utf-8') as f:
                        schema = json.load(f)
                        if schema.get("type") == document_type:
                            schema_for_doc = schema # Store the schema
                            template_name = schema.get("template", f"{document_type}.html")
                            logger.info(f"Found schema '{filename}' for document type '{document_type}'.")
                            break
                except (json.JSONDecodeError, OSError) as e:
                    logger.warning(f"Error reading schema file {filename}: {e}")

    except FileNotFoundError as e:
         logger.error(e)
         raise ValueError(f"Schemas directory error: {e}")
    except Exception as e:
         logger.error(f"Unexpected error loading schemas: {e}", exc_info=True)
         # Continue without schema if needed, or raise error

    if not template_name:
        template_name = f"{document_type}.html"
        logger.warning(f"Schema definition for type '{document_type}' not found or missing 'template'. Using default template name: {template_name}")
    if not schema_for_doc:
         logger.warning(f"Could not load schema definition for type '{document_type}'. Filename generation will use default pattern.")


    logger.info(f"Using template: {template_name}")

    # Load template with error handling
    try:
        # Assume templates/html is relative to project root
        project_root_dir = Path(__file__).resolve().parent.parent
        template_dir_path = project_root_dir / "templates" / "html"
        if not template_dir_path.is_dir():
             raise FileNotFoundError(f"Template directory not found: {template_dir_path}")
        template_loader = jinja2.FileSystemLoader(searchpath=str(template_dir_path))
        jinja_env = jinja2.Environment(loader=template_loader, autoescape=jinja2.select_autoescape(['html', 'xml']))
        template = jinja_env.get_template(template_name)
    except jinja2.exceptions.TemplateNotFound:
        raise ValueError(f"Template not found: {template_dir_path / template_name}")
    except jinja2.exceptions.TemplateError as e:
        raise ValueError(f"Template error in {template_name}: {e}")
    except FileNotFoundError as e:
         raise ValueError(f"Template directory error: {e}")


    # Load images from template directory and convert to base64
    template_dir_path_str = str(template_dir_path) # For os.path functions
    images = {}
    if os.path.isdir(template_dir_path_str):
        for img_ext in [".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp"]:
            for img_file in os.listdir(template_dir_path_str):
                if img_file.lower().endswith(img_ext):
                    img_path = os.path.join(template_dir_path_str, img_file)
                    try:
                        with open(img_path, "rb") as image_file:
                            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")

                        ext = os.path.splitext(img_file)[1].lower()
                        mime_type_map = {
                            '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
                            '.gif': 'image/gif', '.svg': 'image/svg+xml', '.webp': 'image/webp'
                        }
                        mime_type = mime_type_map.get(ext, 'application/octet-stream')

                        images[img_file] = f"data:{mime_type};base64,{encoded_string}"
                        logger.debug(f"Loaded image {img_file} as base64")
                    except Exception as e:
                        logger.warning(f"Error encoding image {img_path} to base64: {e}")
    else:
         logger.warning(f"Template image directory not found: {template_dir_path_str}")


    # Get data from database
    try:
        table_hash, columns, data = get_table_data(session_hash)
    except Exception as e:
        logger.error(f"Failed to get data from database for session {session_hash}: {e}", exc_info=True)
        raise RuntimeError(f"Failed to get data from database: {e}")


    # Create output directory
    output_dir = os.path.join(session_dir, "html")
    try:
        os.makedirs(output_dir, exist_ok=True)
    except OSError as e:
        logger.error(f"Failed to create HTML output directory {output_dir}: {e}")
        raise RuntimeError(f"Failed to create HTML output directory: {e}")


    # Delete all existing HTML files in the output directory
    logger.info(f"Cleaning up existing HTML files in {output_dir}")
    deleted_count = 0
    try:
        for file in os.listdir(output_dir):
            if file.lower().endswith(".html"):
                try:
                    os.remove(os.path.join(output_dir, file))
                    deleted_count += 1
                except Exception as e:
                    logger.warning(f"Error removing existing HTML file {file}: {e}")
        logger.info(f"Removed {deleted_count} existing HTML files from {output_dir}")
    except OSError as e:
         logger.error(f"Error cleaning HTML directory {output_dir}: {e}")


    # --- Database Setup ---
    db_conn = None
    generated_table_name = f"generated_{table_hash}"
    try:
        db_path = os.path.join(session_dir, "data.db")
        db_conn = sqlite3.connect(db_path, timeout=10)
        cursor = db_conn.cursor()

        # Create generated_{table_hash} table if not exists
        cursor.execute(f'''
        CREATE TABLE IF NOT EXISTS {generated_table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            document_type TEXT NOT NULL,
            mime_type TEXT NOT NULL,
            input_file TEXT NOT NULL,
            row INTEGER NOT NULL,
            data TEXT NOT NULL,
            lookup_type TEXT, lookup TEXT, lookup_match TEXT, lookup_value TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        ''')
        db_conn.commit() # Commit table creation separately
    except sqlite3.Error as e:
        logger.error(f"Failed to connect or setup table {generated_table_name} in {db_path}: {e}")
        if db_conn:
            db_conn.close()
        raise RuntimeError(f"Database setup failed: {e}")


    # --- Reverse Mapping ---
    reverse_mapping = {}
    for column_name, mapping_info in field_mapping.items():
        if isinstance(mapping_info, dict) and "type" in mapping_info:
            schema_field_name = mapping_info["type"]
            reverse_mapping[column_name] = schema_field_name
            logger.debug(f"Reverse map created: '{column_name}' -> '{schema_field_name}'")
    logger.info(f"Created reverse mapping with {len(reverse_mapping)} entries.")


    # --- Generate HTML for each row ---
    html_files = []
    errors = []
    generated_filenames_in_run = set() # Track filenames used in THIS run

    for i, row in enumerate(data):
        row_num_display = i + 1 # For logging and DB
        try:
            # Create record for Jinja template (Schema Keys) and DB logging (Mapped Data)
            record_for_template = {}
            db_record_data = {}
            for col, value in row.items():
                schema_field_name = reverse_mapping.get(col)
                if schema_field_name:
                    record_for_template[schema_field_name] = value # Use Schema Key for template
                    db_record_data[schema_field_name] = value      # Use Schema Key for DB
                # Also provide original column name access in template if needed
                record_for_template[col] = value

            if i == 0:
                 logger.debug(f"Record keys for template rendering (row 1): {list(record_for_template.keys())}")

            # Generate HTML
            try:
                html = template.render(record=record_for_template) # Pass the constructed record
            except jinja2.exceptions.TemplateError as e:
                error = f"Template rendering error for row {row_num_display}: {e}"
                logger.error(error)
                errors.append({"row": row_num_display, "error": error})
                continue # Skip this row

            # Replace image src attributes
            for img_file, img_data in images.items():
                if img_data:
                    img_pattern = re.compile(rf'src\s*=\s*["\']?{re.escape(img_file)}["\']?')
                    img_replace = f'src="{img_data}"'
                    html = img_pattern.sub(img_replace, html)

            # Create unique filename
            try:
                # Pass schema_for_doc which might be None
                base_filename = create_filename(record_for_template, document_type, row_num_display, schema_for_doc)
            except Exception as e:
                logger.warning(f"Error creating base filename for row {row_num_display}: {e}. Using default.")
                base_filename = f"{document_type}_{row_num_display:04d}.html"

            filename = base_filename
            file_path = os.path.join(output_dir, filename)
            counter = 1
            base_name, extension = os.path.splitext(base_filename)

            while filename in generated_filenames_in_run or os.path.exists(file_path):
                logger.warning(f"Filename '{filename}' already exists or used in this run. Generating unique name.")
                filename = f"{base_name}_{counter}{extension}"
                file_path = os.path.join(output_dir, filename)
                counter += 1
                if counter > 100:
                    logger.error(f"Could not generate a unique filename for base '{base_name}' after 100 attempts.")
                    # Fallback to a name less likely to collide
                    filename = f"{base_name}_DUPLICATE_{row_num_display}_{int(time.time())}{extension}"
                    file_path = os.path.join(output_dir, filename)
                    if filename in generated_filenames_in_run or os.path.exists(file_path):
                         # Extremely unlikely, but log an error and skip DB insert?
                         error = f"FATAL: Could not generate ANY unique filename for row {row_num_display}"
                         logger.error(error)
                         errors.append({"row": row_num_display, "error": error})
                         continue # Skip writing file and DB insert for this row
                    break

            generated_filenames_in_run.add(filename)

            # Write the unique file
            try:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(html)
            except OSError as e:
                 error = f"Failed to write HTML file {filename} for row {row_num_display}: {e}"
                 logger.error(error)
                 errors.append({"row": row_num_display, "error": error})
                 generated_filenames_in_run.remove(filename) # Remove from set if write failed
                 continue # Skip DB insert

            # Save document metadata to database
            try:
                cursor.execute(
                    f"INSERT INTO {generated_table_name} (document_type, mime_type, input_file, row, data) VALUES (?, ?, ?, ?, ?)",
                    (
                        document_type,
                        "text/html",
                        input_file,
                        row_num_display,
                        json.dumps(db_record_data) # Log the mapped data using schema keys
                    )
                )
                # Commit per row or in batches? Per row is safer but slower.
                db_conn.commit()
                html_files.append(filename)
                logger.info(f"Generated unique HTML file: {filename}")
            except sqlite3.Error as e:
                logger.error(f"Database error saving metadata for row {row_num_display} (file: {filename}): {e}")
                errors.append({"row": row_num_display, "error": f"Database error: {e}"})
                # Don't rollback if previous commits were successful, just log error for this row
                # db_conn.rollback() # Only if committing at end

        except Exception as e:
            logger.error(f"General error generating HTML for row {row_num_display}: {e}", exc_info=True)
            errors.append({"row": row_num_display, "error": str(e)})

    # --- Cleanup and Final Steps ---
    if db_conn:
        db_conn.close()
        logger.debug("Database connection closed.")

    # Update session status
    try:
        update_session_status(
            session_hash,
            file_path=input_file,
            document_type=document_type, # Ensure doc type is persisted
            operation="GENERATE_HTML"
        )
    except Exception as e:
        logger.error(f"Failed to update session status after HTML generation: {e}")


    # Log HTML generation summary
    log_file = None
    try:
        html_logger = HTMLLogger(session_hash)
        log_file = html_logger.log_html_generation(
            num_files=len(html_files),
            file_list=html_files,
            errors=errors
        )
    except Exception as e:
         logger.error(f"Failed to generate HTML summary log: {e}")


    logger.info(f"HTML generation complete for session {session_hash}. Success: {len(html_files)}, Errors: {len(errors)}.")

    return {
        "num_files": len(html_files),
        "html_files": html_files,
        "errors": errors,
        "output_dir": output_dir,
        "log_file": log_file
    }

def create_filename(record: Dict[str, Any], document_type: str, row_number: int, schema: Optional[Dict[str, Any]] = None) -> str:
    """
    Create a filename for the HTML file based on record data and schema pattern.

    Args:
        record: Record data (keys are schema field names)
        document_type: Type of document
        row_number: Row number for fallback
        schema: The loaded schema dictionary (optional)

    Returns:
        Filename for the HTML file (without sequence suffix initially)
    """
    # Default filename pattern
    filename = f"{document_type}_{row_number:04d}.html" # Add padding to row number

    if schema and "output_doc_name" in schema:
        pattern = schema["output_doc_name"]
        logger.info(f"Using output filename pattern: {pattern}")
        logger.debug(f"Available record keys for filename: {list(record.keys())}")

        # Replace {datetime}
        if "{datetime}" in pattern:
            now = datetime.now().strftime("%Y%m%d%H%M%S")
            pattern = pattern.replace("{datetime}", now)

        # Replace {HTML|PDF} with html (lowercase)
        pattern = re.sub(r'\{HTML\|PDF\}', 'html', pattern, flags=re.IGNORECASE)

        # Find placeholders like {FIELD_NAME}
        placeholders = re.findall(r'\{([A-Za-z0-9_]+)\}', pattern)

        for placeholder in placeholders:
            value = record.get(placeholder) # Get value using schema field name key

            if value is not None:
                value_str = str(value).strip()
                sanitized_value = sanitize_filename_value(value_str)
                if sanitized_value: # Don't replace with empty string if sanitation removes everything
                    # Make replacement safe for regex special chars if needed, but simple replace is usually fine here
                    pattern = pattern.replace(f"{{{placeholder}}}", sanitized_value)
                    logger.debug(f"Replaced placeholder {{{placeholder}}} with '{sanitized_value}'")
                else:
                    logger.warning(f"Sanitized value for placeholder {{{placeholder}}} is empty. Original: '{value_str}'. Placeholder replaced with placeholder name.")
                    # Replace with placeholder name to indicate missing value but keep structure
                    pattern = pattern.replace(f"{{{placeholder}}}", f"{placeholder}_EMPTY")
            else:
                logger.warning(f"Placeholder {{{placeholder}}} not found in record data.")
                # Replace with placeholder name to indicate missing value but keep structure
                pattern = pattern.replace(f"{{{placeholder}}}", f"{placeholder}_MISSING")


        # Clean up separators if placeholders were missing/empty
        pattern = re.sub(r'__+', '_', pattern) # Replace multiple underscores with one
        pattern = pattern.strip('_') # Remove leading/trailing underscores

        # Ensure .html extension
        if not pattern.lower().endswith('.html'):
            # Remove existing extension if present before adding .html
            base_pattern, _ = os.path.splitext(pattern)
            pattern = base_pattern + '.html'

        # Basic sanity check for filename length and characters
        base_pattern_name = os.path.basename(pattern) # Check just the filename part
        if len(base_pattern_name) > 200: # Limit length (adjust as needed for filesystem)
             base_pattern_name = base_pattern_name[:195] + ".html"
             pattern = base_pattern_name # Update pattern if truncated

        # Allow a wider range of characters, but log potential issues
        # Filesystems handle many characters, but some can be problematic in URLs/scripts
        if not re.match(r'^[\w\s\-\.\(\)]+$', base_pattern_name): # Allow word chars, space, hyphen, dot, parentheses
             logger.warning(f"Generated filename '{base_pattern_name}' may contain potentially problematic characters.")

        filename = pattern # Use the generated pattern

    else:
         logger.info(f"No 'output_doc_name' pattern found in schema. Using default: {filename}")


    logger.info(f"Base filename for row {row_number}: {filename}")
    return filename


def sanitize_filename_value(value: str) -> str:
    """
    Sanitize a value to be used in a filename.
    Allows letters, numbers, underscore, hyphen, period, parentheses, and space.
    Replaces other invalid characters with a hyphen.

    Args:
        value: The value to sanitize

    Returns:
        Sanitized value safe for use in filenames
    """
    # Keep alphanumeric, underscore, hyphen, period, parentheses, space
    # Replace others with hyphen
    sanitized = re.sub(r'[^\w\s\-\.\(\)]', '-', value)

    # Replace multiple hyphens or spaces with a single one
    sanitized = re.sub(r'[\s-]+', '-', sanitized)

    # Trim leading/trailing whitespace, hyphens, dots
    sanitized = sanitized.strip('. -')

    # Limit length to prevent excessively long filenames (adjust limit as needed)
    max_length = 100
    if len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
        # Ensure it doesn't end with a hyphen after truncation
        sanitized = sanitized.rstrip('-')

    return sanitized

def validate_html_files(session_hash: str, html_files: List[str], html_dir: str) -> str:
    """
    Validate generated HTML files against expected structure.

    Args:
        session_hash: Session hash
        html_files: List of HTML files
        html_dir: Directory containing HTML files

    Returns:
        Path to validation summary file
    """
    # Placeholder for validation logic
    # In a real implementation, this would check for required elements, structure, etc.

    validation_results = []
    for html_file in html_files:
        file_path = os.path.join(html_dir, html_file)
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Simple validation - check for basic HTML structure
            html_valid = content.strip().startswith('<') and content.strip().endswith('>')
            head_valid = '<head>' in content and '</head>' in content
            body_valid = '<body>' in content and '</body>' in content

            validation_results.append({
                "file": html_file,
                "html_valid": html_valid,
                "head_valid": head_valid,
                "body_valid": body_valid,
                "valid": html_valid and head_valid and body_valid
            })
        except Exception as e:
            validation_results.append({
                "file": html_file,
                "valid": False,
                "error": str(e)
            })

    # Create validation summary file
    summary_dir = os.path.join(get_session_dir(session_hash), "logs")
    os.makedirs(summary_dir, exist_ok=True)
    summary_file = os.path.join(summary_dir, "html_validation.json")

    with open(summary_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "html_files": len(html_files),
            "valid_files": sum(1 for r in validation_results if r.get("valid", False)),
            "results": validation_results
        }, f, indent=2)

    return summary_file