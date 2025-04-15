#!/usr/bin/env python
# commands.py
"""
Command Registry Update - Adding user management commands.
This should be integrated into your existing commands.py file.
"""

import logging
from typing import Dict, List, Callable, Any, Optional
import click

# Import existing command functions - KEEP YOUR EXISTING IMPORTS
from core.importer import import_file, get_table_data, get_column_info
from core.validator import validate_data
from core.mapper import generate_mapping_file, delete_mapping_file, update_mapping
from core.html_generator import generate_html_files
from core.pdf_generator import generate_pdfs
from core.session import create_output_dir, get_current_session, update_session_status, get_sessions_data, perform_session_activation

# Import user management functions
from core.auth.auth_db_manager import (
    create_user, list_users, change_user_password, change_user_role,
    update_user_status, delete_user
)

# Import lookup resolver function
from core.lookup_resolver import resolve_lookups as core_resolve_lookups

# Import reporting system functions
from core.reporter import generate_all_reports, rerun_report, list_reports

logger = logging.getLogger(__name__)


def get_table_data_command() -> Dict[str, Any]:
    """
    Get all columns from the database table for the current session.

    Returns:
        Dict with table name and columns
    """
    # Get current session
    session_hash = get_current_session()
    if not session_hash:
        raise ValueError("No active session found")

    # Get table data
    try:
        table_name, columns, _ = get_table_data(session_hash)
        return {
            "table_name": table_name,
            "columns": columns
        }
    except Exception as e:
        logger.error(f"Error getting table data: {e}")
        raise ValueError(f"Failed to get table data: {str(e)}")


# The activate_session function has been replaced by perform_session_activation in core/session.py
# This function is kept here for reference but is no longer used
# def activate_session(session_hash: str) -> Dict[str, Any]:
#     """
#     Activate a session by updating the status.json file with the provided session hash.
#     This makes the specified session the active one for all operations.
#     """
#     # This function has been replaced by perform_session_activation in core/session.py

# KEEP YOUR EXISTING COMMANDS DICTIONARY
COMMANDS = {
    "import": {
        "func": import_file,
        "args": ["file_path"],
        "description": "Import a CSV/XLSX"
    },
    "validate": {
        "func": validate_data,
        "args": [],
        "description": "Validate Import & Detect Document Type"
    },
    "map": {
        "func": generate_mapping_file,
        "args": [],
        "description": "Generate editable field-type mapping for this session."
    },
    "update_mapping": {
        "func": update_mapping,
        "args": ["field_updates"],
        "description": "Update the field mapping with user-provided changes."
    },
    "delete_mapping": {
        "func": delete_mapping_file,
        "args": [],
        "description": "Delete the current mapping file and create a backup."
    },
    "html": {
        "func": generate_html_files,
        "args": [],
        "description": "Generate HTML files from mapped, validated data."
    },
    "pdf": {
        "func": generate_pdfs,
        "args": [],
        "description": "Generate PDFs from HTML templates."
    },
    "table_data": {
        "func": get_table_data_command,
        "args": [],
        "description": "Get all columns from the database table for the current session."
    },
    "all": {
        "description": "Run all steps in sequence: import, validate, map, html, pdf."
    },
    # ADD NEW USER MANAGEMENT COMMANDS
    "user_add": {
        "func": create_user,
        "args": ["username", "password", "role"],
        "description": "Add a new user to the system"
    },
    "user_list": {
        "func": list_users,
        "args": [],
        "description": "List all users in the system"
    },
    "user_password": {
        "func": change_user_password,
        "args": ["username", "new_password"],
        "description": "Change a user's password"
    },
    "user_role": {
        "func": change_user_role,
        "args": ["username", "new_role"],
        "description": "Change a user's role"
    },
    "user_status": {
        "func": update_user_status,
        "args": ["username", "is_active"],
        "description": "Activate or deactivate a user"
    },
    "user_delete": {
        "func": delete_user,
        "args": ["username"],
        "description": "Delete a user from the system"
    },
    "resolve_lookups": {
        "func": core_resolve_lookups,
        "args": ["session"],
        "description": "Resolve lookups for generated documents"
    },
    # ADD REPORTING COMMANDS
    "report_generate": {
        "func": generate_all_reports,
        "args": [],
        "description": "Generate all reports for the current session"
    },
    "report_rerun": {
        "func": rerun_report,
        "args": ["report_id"],
        "description": "Re-run a previously generated report by its ID"
    },
    "report_list": {
        "func": list_reports,
        "args": [],
        "description": "List all report runs with their status"
    },
    "activate_session": {
        "func": perform_session_activation,
        "args": ["session_hash"],
        "description": "Activate a session by hash, preserving its last operation"
    }
}

# KEEP YOUR EXISTING FUNCTIONS
def run_command(command_name: str, **kwargs) -> Any:
    """
    Execute a command from the registry with the given arguments.

    Args:
        command_name: The name of the command to execute
        **kwargs: Arguments to pass to the command

    Returns:
        The result of the command execution

    Raises:
        CommandNotFoundError: If command doesn't exist
        SessionRequiredError: If no active session exists for commands that need one
        CommandExecutionError: If command execution fails
    """
    if command_name not in COMMANDS:
        raise ValueError(f"Unknown command: {command_name}")

    if command_name == "all":
        return run_all_commands(**kwargs)

    command = COMMANDS[command_name]
    func = command["func"]

    # Special case for user management commands - they don't need a session
    if not command_name.startswith("user_") and command_name != "resolve_lookups":
        # Ensure output directory exists for all commands except import
        if command_name != "import":
            session_hash = get_current_session()
            if not session_hash:
                raise ValueError("No active session. Import a file first.")

            try:
                create_output_dir(session_hash)
            except Exception as e:
                raise RuntimeError(f"Failed to create output directory: {str(e)}")

    # Extract only the arguments needed by the function
    func_args = {k: v for k, v in kwargs.items() if k in command.get("args", [])}

    try:
        logger.info(f"Running command: {command_name}")
        result = func(**func_args)
        logger.info(f"Command {command_name} completed successfully")
        return result
    except Exception as e:
        logger.error(f"Error executing command {command_name}: {str(e)}")
        # Re-raise with more context
        raise RuntimeError(f"Command {command_name} failed: {str(e)}") from e


def run_all_commands(**kwargs) -> Dict[str, Any]:
    """
    Run all commands in sequence.

    Args:
        **kwargs: Arguments for all commands

    Returns:
        Dict of results from each command
    """
    results = {}

    # First run import
    if "file_path" not in kwargs:
        raise ValueError("file_path is required for the import command")

    results["import"] = run_command("import", **kwargs)

    # Then run the rest in sequence
    for cmd in ["validate", "map", "html", "pdf", "resolve_lookups"]:
        results[cmd] = run_command(cmd)

    return results


def list_commands() -> Dict[str, Dict]:
    """
    Get a list of all available commands and their details.

    Returns:
        Dict of command information
    """
    command_info = {}
    for name, details in COMMANDS.items():
        command_info[name] = {
            "args": details.get("args", []),
            "description": details.get("description", "")
        }
    return command_info


@click.command()
@click.option('--session', help='Session hash to use. If not provided, uses the current session.')
def resolve_lookups(session):
    """
    Phase 2: Resolve lookups for generated documents.

    This command attempts to match generated document records with foreign keys
    based on the mapping configuration in the tenant settings.
    """
    click.echo("Starting lookup resolution (Phase 2)...")

    try:
        result = core_resolve_lookups(session)

        if result["status"] == "success":
            click.echo(f"Lookup resolution completed successfully:")
            click.echo(f"  - Records processed: {result['records_processed']}")
            click.echo(f"  - Successful lookups: {result['successful_lookups']}")
            click.echo(f"  - Exceptions: {result['exceptions']}")

            if result["exceptions"] > 0:
                click.echo("\nSome lookups resulted in exceptions.")
                click.echo("Use the TUI, API, or Dashboard to review and resolve these exceptions.")
        else:
            click.echo(f"Error: {result['message']}")

    except Exception as e:
        click.echo(f"Error resolving lookups: {str(e)}")
        return 1

    return 0

@click.command("report_generate")
def report_generate_command():
    """Generate all reports for the current session."""
    try:
        result = run_command("report_generate")
        report_id = result.get("report_id")
        reports_dir = result.get("reports_directory")
        click.echo(f"✅ Reports generated with ID: {report_id}")
        click.echo(f"📂 Reports directory: {reports_dir}")
        click.echo(f"📄 Access the report index at: {reports_dir}/index.html")
    except Exception as e:
        click.echo(f"❌ Error generating reports: {e}")

@click.command("report_rerun")
@click.argument("report_id", required=True)
def report_rerun_command(report_id):
    """Re-run a previously generated report by its ID."""
    try:
        result = run_command("report_rerun", report_id=report_id)
        if result.get("status") == "fresh":
            click.echo(f"✅ Report {report_id} is still fresh, no need to regenerate")
        else:
            new_report_id = result.get("report_id")
            reports_dir = result.get("reports_directory")
            click.echo(f"🔁 Report {report_id} regenerated with new ID: {new_report_id}")
            click.echo(f"📂 Reports directory: {reports_dir}")
            click.echo(f"📄 Access the report index at: {reports_dir}/index.html")
    except Exception as e:
        click.echo(f"❌ Error rerunning report: {e}")

@click.command("report_list")
def report_list_command():
    """List all report runs with their status."""
    try:
        reports = run_command("report_list")
        if not reports:
            click.echo("No reports found")
            return

        click.echo("\nReport Runs:")
        click.echo("-" * 100)
        click.echo(f"{'ID':<12} | {'Session':<12} | {'Created At':<19} | {'Status':<8} | {'Count':<5} | {'Table'}")
        click.echo("-" * 100)

        for report in reports:
            status = "✅ Valid" if report.get("is_fresh") else "❌ Stale"
            click.echo(f"{report['report_id']:<12} | {report['session_hash'][:10]:<12} | {report['created_at'][:19]:<19} | {status:<8} | {report['report_count']:<5} | {report['snapshot_table']}")
    except Exception as e:
        click.echo(f"❌ Error listing reports: {e}")



@click.command("activate_session")
@click.argument("session_hash")
def activate_session_command(session_hash: str):
    """Activate a session by hash."""
    try:
        result = run_command("activate_session", session_hash=session_hash)
        click.echo(f"✅ {result.get('message', 'Session activated successfully')}")
    except Exception as e:
        click.echo(f"❌ Error activating session: {e}")

cli = click.Group()
cli.add_command(resolve_lookups)
cli.add_command(report_generate_command)
cli.add_command(report_rerun_command)
cli.add_command(report_list_command)
cli.add_command(activate_session_command)