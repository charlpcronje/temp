#!/usr/bin/env python
"""
HTML Logger - Generate HTML logs and reports for the document processing system.

"""

import os
import json
import logging
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path
import shutil

import jinja2

from core.session import get_session_dir, get_current_session, generate_execution_id

# Configure standard Python logging
logger = logging.getLogger(__name__)

# Set up Jinja2 environment
template_loader = jinja2.FileSystemLoader(searchpath="templates/logs")
jinja_env = jinja2.Environment(loader=template_loader)


class HTMLLogger:
    """
    HTML Logger - Generate HTML logs and reports for the document processing system.
    """

    def __init__(self, session_hash: Optional[str] = None):
        """
        Initialize the HTML logger for a specific session.

        Args:
            session_hash: Hash of the session to log for, or None to use current session

        Raises:
            ValueError: If no active session found
        """
        if session_hash is None:
            session_hash = get_current_session()
            if not session_hash:
                raise ValueError("No active session found")

        self.session_hash = session_hash
        self.session_dir = get_session_dir(session_hash)
        self.www_dir = os.path.join(self.session_dir, "www")
        self.logs_dir = os.path.join(self.session_dir, "logs")
        self.execution_id = generate_execution_id()

        # Ensure directories exist
        os.makedirs(self.www_dir, exist_ok=True)
        os.makedirs(self.logs_dir, exist_ok=True)

        # Template cache
        self._template_cache = {}

    def _get_template(self, template_name: str) -> jinja2.Template:
        """
        Get a template from cache or load it.

        Args:
            template_name: Name of the template file

        Returns:
            Jinja2 Template object

        Raises:
            TemplateError: If template can't be loaded
        """
        if template_name in self._template_cache:
            return self._template_cache[template_name]

        try:
            template = jinja_env.get_template(template_name)
            self._template_cache[template_name] = template
            return template
        except jinja2.exceptions.TemplateNotFound:
            logger.error(f"Template not found: {template_name}")
            raise
        except jinja2.exceptions.TemplateError as e:
            logger.error(f"Template error: {e}")
            raise

    def log_import(self, file_path: str, table_name: str, num_rows: int,
                  columns: List[str], sample_data: List[Dict[str, Any]], current_year: int,
                  conversion_info: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate HTML log for file import operation.

        Args:
            file_path: Path to the imported file
            table_name: Name of SQLite table created
            num_rows: Number of rows imported
            columns: List of column names
            sample_data: Sample of data rows for preview
            current_year: current year to be displayed
            conversion_info: Information about file encoding conversion

        Returns:
            Path to the generated HTML file
        """
        context = {

            "session_hash": self.session_hash,
            "execution_id": self.execution_id,
        }
        conn = sqlite3.connect(os.path.join(self.session_dir, "data.db"))
        cursor = conn.cursor()
        cursor.execute("SELECT created_at FROM import_meta WHERE file_hash = ?", (self.session_hash,))
        created_at = cursor.fetchone()[0]
        conn.close()
        context = {
             "created_at" : created_at,
            "title": "Import Report",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "session_hash": self.session_hash,
            "execution_id": self.execution_id,
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "table_name": table_name,
            "num_rows": num_rows,
            "columns": columns,
            "sample_data": sample_data[:10],  # Limit to 10 rows for preview
        }
        context["current_year"] = current_year

        # Add encoding conversion information if provided
        if conversion_info:
            context["conversion_info"] = conversion_info
            context["encoding_converted"] = conversion_info.get("converted", False)
            context["original_encoding"] = conversion_info.get("original_encoding", "unknown")
            context["new_encoding"] = conversion_info.get("new_encoding", "utf-8")
            context["line_ending_changes"] = conversion_info.get("line_ending_changes", 0)
        else:
            context["encoding_converted"] = False

        html_file = f"import_{self.execution_id}.html"
        return self._render_template("import.html", html_file, context)

    def log_validation(self, document_type: str, validation_results: Dict[str, Any],
                      field_matches: Dict[str, Any], row_validations: List[Dict[str, Any]]) -> str:
        """
        Generate HTML log for data validation.

        Args:
            document_type: Detected document type
            validation_results: Overall validation results
            field_matches: Field matching results
            row_validations: Per-row validation results

        Returns:
            Path to the generated HTML file
        """
        context = {
            "title": "Validation Report",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "session_hash": self.session_hash,
            "execution_id": self.execution_id,
            "document_type": document_type,
            "validation_results": validation_results,
            "field_matches": field_matches,
            "num_rows": len(row_validations),
            "row_summaries": [self._summarize_row_validation(row) for row in row_validations],
        }

        html_file = f"validate_{self.execution_id}.html"
        summary_path = self._render_template("validate.html", html_file, context)

        # Also generate detailed row validation reports
        for i, row_data in enumerate(row_validations):
            row_context = {
                "title": f"Row {i+1} Validation",
                "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "session_hash": self.session_hash,
                "execution_id": self.execution_id,
                "document_type": document_type,
                "row_index": i+1,
                "row_data": row_data,
            }
            row_file = f"validate_row_{i+1:04d}.html"
            self._render_template("validate_row.html", row_file, row_context)

        return summary_path

    def log_mapping(self, mapping_file: str, mapped_fields: Dict[str, str],
                   schema_fields: Dict[str, Any]) -> str:
        """
        Generate HTML log for field mapping.

        Args:
            mapping_file: Path to the mapping JSON file
            mapped_fields: Dictionary of mapped fields
            schema_fields: Schema fields information

        Returns:
            Path to the generated HTML file
        """
        context = {
            "title": "Field Mapping Report",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "session_hash": self.session_hash,
            "execution_id": self.execution_id,
            "mapping_file": mapping_file,
            "mapped_fields": mapped_fields,
            "schema_fields": schema_fields,
        }

        html_file = f"mapping_{self.execution_id}.html"
        return self._render_template("mapping.html", html_file, context)

    def log_html_generation(self, num_files: int, file_list: List[str],
                        errors: List[Dict[str, Any]] = None) -> str:
        """
        Generate HTML log for HTML file generation.

        Args:
            num_files: Number of HTML files generated
            file_list: List of generated file names
            errors: List of errors encountered during generation

        Returns:
            Path to the generated HTML file
        """
        template_name = "Unknown"  # Default value
        output_dir = os.path.join(self.session_dir, "html")

        # Try to get template name from status
        try:
            with open("status.json", 'r') as f:
                status = json.load(f)
                document_type = status.get("current_state", {}).get("document_type")
                # Use document type to infer template
                if document_type:
                    template_name = f"{document_type}.html"
        except Exception as e:
            logger.warning(f"Could not determine template name: {e}")

        context = {
            "title": "HTML Generation Report",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "session_hash": self.session_hash,
            "execution_id": self.execution_id,
            "num_files": num_files,
            "template_name": template_name,
            "output_dir": output_dir,
            "file_list": file_list,
            "errors": errors or [],
        }

        html_file = f"generate_html_{self.execution_id}.html"
        return self._render_template("generate_html.html", html_file, context)

    def log_pdf_generation(self, num_files: int, conversion_times: List[float],
                          file_list: List[str], errors: List[Dict[str, Any]]) -> str:
        """
        Generate HTML log for PDF generation.

        Args:
            num_files: Number of PDFs generated
            conversion_times: List of conversion times in seconds
            file_list: List of generated PDF file names
            errors: List of any errors encountered

        Returns:
            Path to the generated HTML file
        """
        context = {
            "title": "PDF Generation Report",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "session_hash": self.session_hash,
            "execution_id": self.execution_id,
            "num_files": num_files,
            "total_time": sum(conversion_times),
            "avg_time": sum(conversion_times) / len(conversion_times) if conversion_times else 0,
            "file_list": file_list,
            "errors": errors,
        }

        html_file = f"generate_pdf_{self.execution_id}.html"
        return self._render_template("generate_pdf.html", html_file, context)

    def generate_execution_summary(self, steps_completed: List[str],
                                  stats: Dict[str, Any]) -> str:
        """
        Generate HTML execution summary for the entire process.

        Args:
            steps_completed: List of completed processing steps
            stats: Statistics about the execution

        Returns:
            Path to the generated HTML file
        """
        context = {
            "title": "Execution Summary Report",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "session_hash": self.session_hash,
            "execution_id": self.execution_id,
            "steps_completed": steps_completed,
            "stats": stats,
            "logs": self._collect_log_files(),
            "html_files": self._collect_html_files(),
            "pdf_files": self._collect_pdf_files(),
        }

        html_file = f"execution_summary_{self.execution_id}.html"
        summary_path = self._render_template("execution_summary.html", html_file, context)

        # Create index.html that redirects to the summary
        self._create_index(os.path.basename(summary_path))

        return summary_path

    def generate_validation_summary(self, validation_results: List[Dict[str, Any]]) -> str:
        """
        Generate HTML validation summary across all files.

        Args:
            validation_results: Results from validating all files

        Returns:
            Path to the generated HTML file
        """
        # Calculate summary statistics
        total_files = len(validation_results)
        passed = sum(1 for r in validation_results if r.get("status") == "VALID")
        failed = sum(1 for r in validation_results if r.get("status") == "INVALID")
        errors = total_files - passed - failed

        total_fields = sum(r.get("total_fields", 0) for r in validation_results)
        matching_fields = sum(r.get("matching_fields", 0) for r in validation_results)
        mismatched_fields = sum(r.get("mismatched_fields", 0) for r in validation_results)
        missing_fields = sum(r.get("missing_fields", 0) for r in validation_results)

        match_rate = (matching_fields / total_fields * 100) if total_fields > 0 else 0
        success_rate = (passed / total_files * 100) if total_files > 0 else 0

        context = {
            "title": "HTML Validation Summary Report",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "session_hash": self.session_hash,
            "execution_id": self.execution_id,
            "total_files": total_files,
            "passed": passed,
            "failed": failed,
            "errors": errors,
            "success_rate": success_rate,
            "total_fields": total_fields,
            "matching_fields": matching_fields,
            "mismatched_fields": mismatched_fields,
            "missing_fields": missing_fields,
            "match_rate": match_rate,
            "file_results": validation_results,
        }

        html_file = f"validation_summary_{self.execution_id}.html"
        return self._render_template("validation_summary.html", html_file, context)

    def generate_dashboard(self) -> str:
        """
        Generate the main dashboard HTML page for browsing all reports.

        Returns:
            Path to the generated dashboard HTML file
        """
        # Collect information about all logs and generated files
        logs = self._collect_log_files()
        html_files = self._collect_html_files()
        pdf_files = self._collect_pdf_files()

        # Get execution summaries
        summaries = [log for log in logs if log["file"].startswith("execution_summary_")]
        validation_summaries = [log for log in logs if log["file"].startswith("validation_summary_")]

        context = {
            "title": "Document Processing Dashboard",
            "generated_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "session_hash": self.session_hash,
            "logs": logs,
            "html_files": html_files,
            "pdf_files": pdf_files,
            "summaries": summaries,
            "validation_summaries": validation_summaries,
            "stats": {
                "log_count": len(logs),
                "html_count": len(html_files),
                "pdf_count": len(pdf_files),
            }
        }

        html_file = "dashboard.html"
        dashboard_path = self._render_template("dashboard.html", html_file, context)

        # Create index.html that redirects to the dashboard
        self._create_index(os.path.basename(dashboard_path))

        return dashboard_path

    def _render_template(self, template_name: str, output_file: str,
                        context: Dict[str, Any]) -> str:
        """
        Render a Jinja2 template and save the result to a file.

        Args:
            template_name: Name of the template file
            output_file: Name of the output file
            context: Template context variables

        Returns:
            Path to the generated file
        """
        try:
            # Load template
            template = jinja_env.get_template(template_name)

            # Add common context variables
            context.update({
                "dark_mode_toggle": True,
                "css_path": "assets/style.css",
                "dark_css_path": "assets/dark-style.css",
            })

            # Render template
            rendered_html = template.render(**context)

            # Save to www directory for browser viewing
            www_path = os.path.join(self.www_dir, output_file)
            with open(www_path, 'w') as f:
                f.write(rendered_html)

            # Also save to logs directory for archival
            log_path = os.path.join(self.logs_dir, output_file)
            with open(log_path, 'w') as f:
                f.write(rendered_html)

            logger.info(f"Generated HTML log: {www_path}")
            return www_path

        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}")
            raise

    def _create_index(self, target_file: str) -> str:
        """
        Create an index.html file that redirects to another HTML file.

        Args:
            target_file: Name of the file to redirect to

        Returns:
            Path to the created index.html
        """
        index_path = os.path.join(self.www_dir, "index.html")

        with open(index_path, 'w') as f:
            f.write(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta http-equiv="refresh" content="0; url={target_file}">
    <title>Redirecting to {target_file}</title>
</head>
<body>
    <p>If you are not redirected automatically, follow this <a href="{target_file}">link</a>.</p>
</body>
</html>
""")

        logger.info(f"Created index.html redirecting to {target_file}")
        return index_path

    def _collect_log_files(self) -> List[Dict[str, str]]:
        """
        Collect information about all log files in the session.

        Returns:
            List of dictionaries with information about each log file
        """
        logs = []

        if os.path.exists(self.www_dir):
            for file in os.listdir(self.www_dir):
                if file.endswith(".html") and file != "index.html" and not file.startswith("_"):
                    # Determine type from filename
                    file_type = None
                    if file.startswith("import_"):
                        file_type = "Import Log"
                    elif file.startswith("validate_row_"):
                        file_type = "Row Validation"
                    elif file.startswith("validate_"):
                        file_type = "Validation Log"
                    elif file.startswith("mapping_"):
                        file_type = "Mapping Log"
                    elif file.startswith("generate_html_"):
                        file_type = "HTML Generation Log"
                    elif file.startswith("generate_pdf_"):
                        file_type = "PDF Generation Log"
                    elif file.startswith("execution_summary_"):
                        file_type = "Execution Summary"
                    elif file.startswith("validation_summary_"):
                        file_type = "Validation Summary"
                    else:
                        file_type = "Log"

                    logs.append({
                        "file": file,
                        "path": file,
                        "type": file_type,
                        "date": self._get_file_date(os.path.join(self.www_dir, file))
                    })

        return sorted(logs, key=lambda x: x["date"], reverse=True)

    def _collect_html_files(self) -> List[Dict[str, str]]:
        """
        Collect information about all generated HTML files.

        Returns:
            List of dictionaries with information about each HTML file
        """
        files = []
        html_dir = os.path.join(self.session_dir, "html")

        if os.path.exists(html_dir):
            for file in os.listdir(html_dir):
                if file.endswith(".html"):
                    files.append({
                        "file": file,
                        "path": f"../html/{file}",
                        "date": self._get_file_date(os.path.join(html_dir, file))
                    })

        return sorted(files, key=lambda x: x["date"], reverse=True)

    def _collect_pdf_files(self) -> List[Dict[str, str]]:
        """
        Collect information about all generated PDF files.

        Returns:
            List of dictionaries with information about each PDF file
        """
        files = []
        pdf_dir = os.path.join(self.session_dir, "pdf")

        if os.path.exists(pdf_dir):
            for file in os.listdir(pdf_dir):
                if file.endswith(".pdf"):
                    files.append({
                        "file": file,
                        "path": f"../pdf/{file}",
                        "date": self._get_file_date(os.path.join(pdf_dir, file))
                    })

        return sorted(files, key=lambda x: x["date"], reverse=True)

    def _get_file_date(self, file_path: str) -> str:
        """
        Get the formatted modification date of a file.

        Args:
            file_path: Path to the file

        Returns:
            Formatted date string
        """
        try:
            mtime = os.path.getmtime(file_path)
            return datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")
        except OSError:
            return "Unknown"

    def _summarize_row_validation(self, row_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a summary of row validation results.

        Args:
            row_data: Detailed row validation data

        Returns:
            Summary of validation results for the row
        """
        # Count field matches, mismatches, and missing values
        fields = row_data.get("fields", [])
        total = len(fields)
        matches = sum(1 for f in fields if f.get("status") == "MATCH")
        mismatches = sum(1 for f in fields if f.get("status") == "MISMATCH")
        missing = sum(1 for f in fields if f.get("status") == "MISSING_DATA")

        # Calculate match rate
        match_rate = (matches / total * 100) if total > 0 else 0

        # Determine overall status
        if mismatches > 0:
            status = "INVALID"
        elif missing > 0:
            status = "INCOMPLETE"
        else:
            status = "VALID"

        return {
            "row_id": row_data.get("row_id", "Unknown"),
            "status": status,
            "total_fields": total,
            "matching_fields": matches,
            "mismatched_fields": mismatches,
            "missing_fields": missing,
            "match_rate": match_rate,
        }