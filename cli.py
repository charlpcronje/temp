#!/usr/bin/env python
"""
Command Line Interface for the Document Processing System.
"""

import os
import sys
import logging
from typing import Optional, List, Dict, Any

import typer
from rich.console import Console
from rich.table import Table
from rich.logging import RichHandler

# Import commands
from commands import COMMANDS, run_command, list_commands
from core.symbols import CHECK_MARK

# Set up CLI app
app = typer.Typer(
    name="docproc",
    help="Document Processing System - Process CSV/Excel files into HTML/PDF documents.",
    add_completion=False
)

# Set up Rich console
console = Console()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",
    datefmt="[%X]",
    handlers=[RichHandler(console=console, rich_tracebacks=True)]
)

logger = logging.getLogger("docproc")


# Create a user sub-command group
user_app = typer.Typer(
    name="user",
    help="User management commands",
    add_completion=False
)


@user_app.command("add")
def add_user(
    username: str = typer.Argument(..., help="Username for the new user"),
    password: str = typer.Argument(..., help="Password for the new user"),
    role: str = typer.Option("user", help="Role for the new user (user or admin)")
):
    """
    Add a new user to the system.
    """
    try:
        from core.auth.auth_db_manager import create_user, init_auth_db
        init_auth_db()
        
        # Validate role
        if role not in ["user", "admin"]:
            console.print(f"[bold red]Error:[/bold red] Invalid role. Use 'user' or 'admin'.")
            raise typer.Exit(code=1)
        
        console.print(f"[bold blue]Creating user '{username}'...[/bold blue]")
        result = create_user(username, password, role)
        
        if result:
            console.print(f"[bold green]{CHECK_MARK} User '{username}' created successfully with role '{role}'![/bold green]")
        else:
            console.print(f"[bold red]Error:[/bold red] Failed to create user. Username may already exist.")
            raise typer.Exit(code=1)
            
    except Exception as e:
        console.print(f"[bold red]Error creating user:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@user_app.command("list")
def list_users():
    """
    List all users in the system.
    """
    try:
        from core.auth.auth_db_manager import list_users as db_list_users, init_auth_db
        init_auth_db()
        
        console.print("[bold blue]Listing users...[/bold blue]")
        users = db_list_users()
        
        if users:
            table = Table(title="System Users")
            table.add_column("Username", style="cyan")
            table.add_column("Role", style="green")
            table.add_column("Status", style="yellow")
            table.add_column("Created", style="magenta")
            table.add_column("Last Login", style="blue")
            
            for user in users:
                status = "[green]Active" if user["is_active"] else "[red]Inactive"
                last_login = user["last_login"] or "Never"
                table.add_row(
                    user["username"],
                    user["role"],
                    status,
                    user["created_at"],
                    last_login
                )
                
            console.print(table)
        else:
            console.print("[yellow]No users found in the system.[/yellow]")
            
    except Exception as e:
        console.print(f"[bold red]Error listing users:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@user_app.command("password")
def change_password(
    username: str = typer.Argument(..., help="Username of the user to update"),
    new_password: str = typer.Argument(..., help="New password for the user")
):
    """
    Change a user's password.
    """
    try:
        from core.auth.auth_db_manager import change_user_password, init_auth_db
        init_auth_db()
        
        console.print(f"[bold blue]Changing password for user '{username}'...[/bold blue]")
        result = change_user_password(username, new_password)
        
        if result:
            console.print(f"[bold green]{CHECK_MARK} Password changed successfully for user '{username}'![/bold green]")
        else:
            console.print(f"[bold red]Error:[/bold red] Failed to change password. User may not exist.")
            raise typer.Exit(code=1)
            
    except Exception as e:
        console.print(f"[bold red]Error changing password:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@user_app.command("role")
def change_role(
    username: str = typer.Argument(..., help="Username of the user to update"),
    new_role: str = typer.Argument(..., help="New role for the user (user or admin)")
):
    """
    Change a user's role.
    """
    try:
        from core.auth.auth_db_manager import change_user_role, init_auth_db
        init_auth_db()
        
        # Validate role
        if new_role not in ["user", "admin"]:
            console.print(f"[bold red]Error:[/bold red] Invalid role. Use 'user' or 'admin'.")
            raise typer.Exit(code=1)
        
        console.print(f"[bold blue]Changing role for user '{username}' to '{new_role}'...[/bold blue]")
        result = change_user_role(username, new_role)
        
        if result:
            console.print(f"[bold green]{CHECK_MARK} Role changed successfully for user '{username}'![/bold green]")
        else:
            console.print(f"[bold red]Error:[/bold red] Failed to change role. User may not exist.")
            raise typer.Exit(code=1)
            
    except Exception as e:
        console.print(f"[bold red]Error changing role:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@user_app.command("status")
def change_status(
    username: str = typer.Argument(..., help="Username of the user to update"),
    is_active: bool = typer.Argument(..., help="New status for the user (True for active, False for inactive)")
):
    """
    Activate or deactivate a user.
    """
    try:
        from core.auth.auth_db_manager import update_user_status, init_auth_db
        init_auth_db()
        
        status_str = "activate" if is_active else "deactivate"
        console.print(f"[bold blue]{status_str.capitalize()} user '{username}'...[/bold blue]")
        result = update_user_status(username, is_active)
        
        if result:
            console.print(f"[bold green]{CHECK_MARK} User '{username}' {status_str}d successfully![/bold green]")
        else:
            console.print(f"[bold red]Error:[/bold red] Failed to {status_str} user. User may not exist.")
            raise typer.Exit(code=1)
            
    except Exception as e:
        console.print(f"[bold red]Error updating user status:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@user_app.command("delete")
def delete_user(
    username: str = typer.Argument(..., help="Username of the user to delete"),
    force: bool = typer.Option(False, "--force", "-f", help="Force deletion without confirmation")
):
    """
    Delete a user from the system.
    """
    try:
        from core.auth.auth_db_manager import delete_user as db_delete_user, init_auth_db
        init_auth_db()
        
        # Confirm deletion
        if not force and not typer.confirm(f"Are you sure you want to delete user '{username}'?"):
            console.print("[yellow]User deletion cancelled.[/yellow]")
            return
        
        console.print(f"[bold blue]Deleting user '{username}'...[/bold blue]")
        result = db_delete_user(username)
        
        if result:
            console.print(f"[bold green]{CHECK_MARK} User '{username}' deleted successfully![/bold green]")
        else:
            console.print(f"[bold red]Error:[/bold red] Failed to delete user. User may not exist.")
            raise typer.Exit(code=1)
            
    except Exception as e:
        console.print(f"[bold red]Error deleting user:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command("import")
def import_file(
    file_path: str = typer.Argument(..., help="Path to the CSV or Excel file to import"),
    output_dir: Optional[str] = typer.Option(None, "--output", "-o", help="Custom output directory"),
    chunk_size: int = typer.Option(10000, "--chunk-size", "-c", help="Number of rows to process at once (for large files)"),
    force: bool = typer.Option(False, "--force", "-f", help="Force reimport even if file was imported before")
):
    """
    Import a CSV or Excel file into the system.
    
    The file will be hashed and stored in a SQLite database with a unique session ID.
    This is the first step in the document processing workflow.
    """
    try:
        # Validate file exists
        if not os.path.isfile(file_path):
            console.print(f"[bold red]Error:[/bold red] File not found: {file_path}")
            raise typer.Exit(code=1)
        
        # Check file size and warn if large
        file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
        if file_size_mb > 50:  # 50 MB threshold
            console.print(f"[yellow]Warning: Large file detected ({file_size_mb:.1f} MB). Import may take some time.[/yellow]")
            if not force and not typer.confirm("Continue with import?"):
                raise typer.Exit()
        
        with console.status(f"[bold blue]Importing file: {file_path}[/bold blue]", spinner="dots"):
            # Add custom output directory handling if specified
            if output_dir:
                # TODO: Implement custom output directory
                console.print(f"[yellow]Warning: Custom output directory not implemented yet.[/yellow]")
            
            result = run_command("import", file_path=file_path)
        
        if result:
            console.print(f"[bold green]{CHECK_MARK} File imported successfully![/bold green]")
            console.print(f"Session hash: {result['session_hash']}")
            console.print(f"Imported {result['num_rows']} rows with {len(result['columns'])} columns")
            console.print(f"Output directory: {result['session_dir']}")
            console.print(f"Web dashboard: file://{os.path.abspath(os.path.join(result['session_dir'], 'www', 'index.html'))}")
            return result
        
    except Exception as e:
        console.print(f"[bold red]Error importing file:[/bold red] {str(e)}")
        if verbose:
            console.print_exception()
        raise typer.Exit(code=1)
        

@app.command("validate")
def validate_data():
    """
    Validate the imported data and detect document type.
    """
    try:
        console.print("[bold blue]Validating data...[/bold blue]")
        result = run_command("validate")
        
        if result:
            validation_results = result["validation_results"]
            
            console.print(f"[bold green]{CHECK_MARK} Validation complete![/bold green]")
            console.print(f"Detected document type: [bold]{validation_results['document_type']}[/bold]")
            console.print(f"Match score: {validation_results['match_score']:.2f}%")
            console.print(f"Valid rows: {validation_results['valid_rows']} of {validation_results['total_rows']} ({validation_results['success_rate']:.2f}%)")
            
            return result
        
    except Exception as e:
        console.print(f"[bold red]Error validating data:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command("map")
def generate_mapping():
    """
    Generate field mapping file.
    """
    try:
        console.print("[bold blue]Generating field mapping...[/bold blue]")
        result = run_command("map")
        
        if result:
            console.print(f"[bold green]{CHECK_MARK} Mapping file generated![/bold green]")
            console.print(f"Mapping file: {result['mapping_file']}")
            
            # Display mapped fields
            table = Table(title="Field Mapping")
            table.add_column("Field", style="cyan")
            table.add_column("Column", style="green")
            
            for field, column in result["mapped_fields"].items():
                table.add_row(field, column)
            
            console.print(table)
            
            return result
        
    except Exception as e:
        console.print(f"[bold red]Error generating mapping:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command("html")
def generate_html():
    """
    Generate HTML files from the mapped data.
    """
    try:
        console.print("[bold blue]Generating HTML files...[/bold blue]")
        result = run_command("html")
        
        if result:
            console.print(f"[bold green]{CHECK_MARK} HTML files generated![/bold green]")
            console.print(f"Generated {result['num_files']} HTML files")
            console.print(f"Output directory: {result['output_dir']}")
            
            if result["errors"]:
                console.print(f"[bold yellow]⚠ {len(result['errors'])} errors occurred during generation[/bold yellow]")
            
            return result
        
    except Exception as e:
        console.print(f"[bold red]Error generating HTML:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command("pdf")
def generate_pdf():
    """
    Generate PDF files from HTML files.
    """
    try:
        console.print("[bold blue]Generating PDF files...[/bold blue]")
        result = run_command("pdf")
        
        if result:
            console.print(f"[bold green]{CHECK_MARK} PDF files generated![/bold green]")
            console.print(f"Generated {result['num_files']} PDF files")
            
            if result["errors"]:
                console.print(f"[bold yellow]⚠ {len(result['errors'])} errors occurred during generation[/bold yellow]")
            
            return result
        
    except Exception as e:
        console.print(f"[bold red]Error generating PDFs:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command("all")
def run_all_steps(
    file_path: str = typer.Argument(..., help="Path to the CSV or Excel file to import")
):
    """
    Run all processing steps in sequence.
    """
    try:
        # Import file
        import_result = import_file(file_path)
        if not import_result:
            return
        
        # Validate data
        validate_result = validate_data()
        if not validate_result:
            return
        
        # Generate mapping
        mapping_result = generate_mapping()
        if not mapping_result:
            return
        
        # Generate HTML
        html_result = generate_html()
        if not html_result:
            return
        
        # Generate PDF
        pdf_result = generate_pdf()
        if not pdf_result:
            return
        
        console.print(f"\n[bold green]{CHECK_MARK} All steps completed successfully![/bold green]")
        console.print(f"Output directory: {import_result['session_dir']}")
        console.print(f"View the dashboard at: {import_result['session_dir']}/www/index.html")
        
    except Exception as e:
        console.print(f"[bold red]Error running all steps:[/bold red] {str(e)}")
        raise typer.Exit(code=1)


@app.command("list")
def list_available_commands():
    """
    List all available commands.
    """
    commands = list_commands()
    
    table = Table(title="Available Commands")
    table.add_column("Command", style="cyan")
    table.add_column("Description", style="green")
    table.add_column("Arguments", style="yellow")
    
    for name, info in commands.items():
        args = ", ".join(info.get("args", []))
        table.add_row(name, info.get("description", ""), args or "-")
    
    console.print(table)


@app.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    quiet: bool = typer.Option(False, "--quiet", "-q", help="Suppress all output except errors"),
):
    """
    Document Processing System - Process CSV/Excel files into HTML/PDF documents.
    """
    # Set logging level based on verbosity
    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    elif quiet:
        logging.getLogger().setLevel(logging.ERROR)
    else:
        logging.getLogger().setLevel(logging.INFO)


if __name__ == "__main__":
    # Add the user commands sub-app to the main app
    app.add_typer(user_app, name="user")
    app()