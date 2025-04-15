#!/usr/bin/env python
"""
Textual TUI for the Document Processing System.
"""

import os
import sys
import json
import logging
import io
import subprocess
import webbrowser
from typing import Any, Dict, List, Optional, Type
from contextlib import redirect_stdout, redirect_stderr
from pathlib import Path
from datetime import datetime
from rich.text import Text

# Ensure core modules can be imported
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from rich.text import Text
from rich.panel import Panel
from rich.console import RenderableType
from rich.table import Table

from textual.app import App, ComposeResult, CSSPathType
from textual.containers import Container, VerticalScroll, Horizontal
from textual.reactive import reactive
from textual.widgets import (
    Header, Footer, Static, ListView, ListItem, Log, Input, Button, Label,
    DataTable, Select
)
from textual.message import Message
from textual.screen import ModalScreen, Screen
from textual.widgets.tree import TreeNode
import textwrap

# Import from existing project structure
try:
    from commands import COMMANDS, run_command, list_commands
    from core.session import get_current_session, get_session_dir, load_config, STATUS_FILE
    from core.logger import HTMLLogger  # Although not directly used, ensure it's importable
    from core.symbols import CHECK_MARK  # Import the CHECK_MARK symbol
    # Import reporting system functions
    from core.reporter import generate_all_reports, rerun_report, list_reports
except ImportError as e:
    print(f"Error importing core modules: {e}")
    print("Please ensure tui.py is in the project root directory alongside 'core' and 'commands.py'.")
    sys.exit(1)

# --- Configuration ---
CSS = """
Screen {
    layers: base modals; /* Define layers */
}

#app-grid {
    grid-size: 2;
    grid-gutter: 1 2;
    grid-rows: 1fr auto; /* Top row takes available space, bottom row auto-sizes */
    padding: 1;
}

#commands-list {
    border: round $accent;
    width: 30;
    height: 100%;
    margin-right: 1;
}

#details-panel {
    border: round $accent;
    height: 100%;
    padding: 1;
}

#log-panel {
    border: round $accent;
    column-span: 2;
    margin-top: 1;
    height: 15;
    overflow-y: scroll;
}

ArgumentModal {
    align: center middle;
}

#modal-container {
    width: 60;
    height: auto;
    max-height: 80%;
    background: $surface;
    border: thick $accent;
    padding: 1 2;
}

#modal-container Label {
    margin-top: 1;
}

#modal-buttons {
    width: 100%;
    align-horizontal: right;
    margin-top: 1;
}

#modal-buttons Button {
    margin-left: 1;
}
"""

# --- Widgets ---

class CommandItem(ListItem):
    """A ListItem that holds command information."""
    def __init__(self, name: str, info: Dict[str, Any]) -> None:
        super().__init__()
        self.command_name = name
        self.command_info = info
        self.description = info.get("description", name.capitalize())

    def compose(self) -> ComposeResult:
        yield Label(self.command_name.capitalize(), id="command-label")
        yield Label(self.description, id="command-desc")


class TuiHandler(logging.Handler):
    """A logging handler that sends records to a Textual Log widget."""
    def __init__(self, log_widget: Log):
        super().__init__()
        self.log_widget = log_widget

    def emit(self, record: logging.LogRecord):
        try:
            msg = self.format(record)
            self.log_widget.write(msg)
        except Exception:
            self.handleError(record)


# --- Modal Screen for Arguments ---

class ArgumentModal(ModalScreen[Dict[str, Any]]):
    """Modal screen to collect arguments for a command."""

    # Custom message to send results back
    class Submitted(Message):
        def __init__(self, command_name: str, args: Dict[str, Any]) -> None:
            self.command_name = command_name
            self.args = args
            super().__init__()

    def __init__(
        self,
        command_name: str,
        required_args: List[str],
        name: str | None = None,
        id: str | None = None,
        classes: str | None = None,
    ) -> None:
        super().__init__(name, id, classes)
        self.command_name = command_name
        self.required_args = required_args
        self.inputs: Dict[str, Input] = {}

    def compose(self) -> ComposeResult:
        with Container(id="modal-container"):
            yield Label(f"[bold]Arguments for '{self.command_name}'[/bold]")
            with VerticalScroll():
                for arg_name in self.required_args:
                    # Special handling for file_path to suggest relative paths if needed
                    placeholder = "Enter path..." if "path" in arg_name else f"Enter {arg_name}..."
                    input_widget = Input(placeholder=placeholder, name=arg_name)
                    self.inputs[arg_name] = input_widget
                    yield Label(f"{arg_name.replace('_', ' ').capitalize()}:")
                    yield input_widget

            with Horizontal(id="modal-buttons"):
                yield Button("Run Command", variant="primary", id="run")
                yield Button("Cancel", id="cancel")

    def on_mount(self) -> None:
        """Focus the first input field when the modal appears."""
        if self.inputs:
            first_input = next(iter(self.inputs.values()))
            self.set_focus(first_input)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "run":
            collected_args = {name: input_widget.value for name, input_widget in self.inputs.items()}
            # Basic validation: Check if required fields are filled
            missing = [name for name, value in collected_args.items() if not value]
            if missing:
                # Ideally, show an error message within the modal
                self.app.bell()
                self.query_one(f"#{missing[0]}").focus()  # Focus the first missing field
                return
            # Send collected args back to the main app
            self.post_message(self.Submitted(self.command_name, collected_args))
            self.dismiss(collected_args)
        elif event.button.id == "cancel":
            self.dismiss()


# --- Reports Screen ---

class ReportItem(ListItem):
    """A ListItem that holds report information."""
    
    def __init__(self, report_data: Dict[str, Any]) -> None:
        super().__init__()
        self.report_data = report_data
        self.report_id = report_data.get("report_id", "Unknown")
        self.session_hash = report_data.get("session_hash", "Unknown")
        self.created_at = report_data.get("created_at", "Unknown")
        self.is_fresh = report_data.get("is_fresh", False)
        
    def compose(self) -> ComposeResult:
        status = "✅ Valid" if self.is_fresh else "❌ Stale"
        yield Label(self.report_id, id="report-id")
        yield Label(f"{self.created_at[:19]} - {status}", id="report-status")


class ReportsScreen(Screen):
    """Screen for viewing and managing reports."""
    
    BINDINGS = [
        ("r", "refresh", "Refresh"),
        ("g", "generate", "Generate"),
        ("v", "view_report", "View"),
        ("escape", "app.pop_screen", "Back"),
    ]
    
    reports = reactive(None)
    selected_report = reactive(None)
    
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        
        with Container(id="reports-grid"):
            with Container(id="reports-list-container"):
                yield Static("Reports", id="reports-title")
                yield Button("Generate New Report", id="generate-btn", variant="primary")
                yield Button("Refresh List", id="refresh-btn")
                yield ListView(id="reports-list")
            
            with Container(id="report-details-container"):
                yield Static("Report Details", id="report-details-title")
                yield VerticalScroll(Static("Select a report to view details", id="report-details"))
                
                with Horizontal(id="action-buttons"):
                    yield Button("View HTML", id="view-html-btn", disabled=True)
                    yield Button("View PDF", id="view-pdf-btn", disabled=True)
                    yield Button("Rerun Report", id="rerun-btn", disabled=True)
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Load reports when the screen is mounted."""
        self.load_reports()
    
    def load_reports(self) -> None:
        """Load reports from the database."""
        try:
            self.reports = run_command("report_list")
            self.refresh_reports_list()
            self.app.log.info("Reports loaded successfully")
        except Exception as e:
            self.app.log.error(f"Error loading reports: {e}")
    
    def refresh_reports_list(self) -> None:
        """Refresh the reports list with current data."""
        reports_list = self.query_one("#reports-list", ListView)
        reports_list.clear()
        
        # Check if reports is a list
        if not self.reports:
            reports_list.append(ListItem(Label("No reports found")))
            return
        
        # Sort reports by creation date (newest first)
        sorted_reports = sorted(
            self.reports,
            key=lambda r: r.get("created_at", ""),
            reverse=True
        )
        
        for report in sorted_reports:
            reports_list.append(ReportItem(report))
    
    def update_report_details(self, report_data: Dict[str, Any]) -> None:
        """Update the report details panel with selected report info."""
        details_panel = self.query_one("#report-details", Static)
        
        if not report_data:
            details_panel.update("No report selected")
            return
        
        # Create a rich table for report details
        table = Table(title=f"Report: {report_data['report_id']}")
        table.add_column("Property")
        table.add_column("Value")
        
        # Add rows for each property
        table.add_row("Report ID", report_data["report_id"])
        table.add_row("Session Hash", report_data["session_hash"])
        table.add_row("Created At", report_data["created_at"])
        table.add_row("Status", "✅ Valid" if report_data["is_fresh"] else "❌ Stale")
        table.add_row("Snapshot Table", report_data["snapshot_table"])
        table.add_row("Report Count", str(report_data.get("report_count", 0)))
        
        # Update buttons based on report status
        self.query_one("#view-html-btn", Button).disabled = False
        self.query_one("#view-pdf-btn", Button).disabled = False
        self.query_one("#rerun-btn", Button).disabled = False
        
        details_panel.update(table)
    
    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle report selection."""
        item = event.item
        if isinstance(item, ReportItem):
            self.selected_report = item.report_data
            self.update_report_details(item.report_data)
    
    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id
        
        if button_id == "generate-btn":
            self.action_generate()
        
        elif button_id == "refresh-btn":
            self.action_refresh()
        
        elif button_id == "view-html-btn" and self.selected_report:
            self.view_report_html()
        
        elif button_id == "view-pdf-btn" and self.selected_report:
            self.view_report_pdf()
        
        elif button_id == "rerun-btn" and self.selected_report:
            self.rerun_report()
    
    def action_refresh(self) -> None:
        """Refresh the reports list."""
        self.load_reports()
    
    def action_generate(self) -> None:
        """Generate a new report."""
        try:
            self.app.log.info("Generating new reports...")
            result = run_command("report_generate")
            self.app.log.info(f"Reports generated with ID: {result.get('report_id')}")
            self.load_reports()
        except Exception as e:
            self.app.log.error(f"Error generating reports: {e}")
    
    def action_view_report(self) -> None:
        """View the selected report HTML."""
        if self.selected_report:
            self.view_report_html()
    
    def view_report_html(self) -> None:
        """Open the selected report HTML in a browser."""
        if not self.selected_report:
            return
        
        try:
            # Get the session and report directories
            session_hash = get_current_session()
            if not session_hash:
                self.app.log.error("No active session found")
                return
            
            # Find the report directory
            session_dir = get_session_dir(session_hash)
            reports_dir = os.path.join(session_dir, "reports")
            
            # Find the report directory by traversing directories that start with "hash"
            report_dir = None
            report_id = self.selected_report.get("report_id")
            
            for dir_name in os.listdir(reports_dir):
                if dir_name.startswith("hash"):
                    meta_path = os.path.join(reports_dir, dir_name, "meta.json")
                    if os.path.exists(meta_path):
                        with open(meta_path, 'r') as f:
                            meta = json.load(f)
                            if meta.get("report_id") == report_id:
                                report_dir = os.path.join(reports_dir, dir_name)
                                break
            
            if not report_dir:
                self.app.log.error(f"Report directory not found for report ID: {report_id}")
                return
            
            # Open the index.html file in the default browser
            index_path = os.path.join(report_dir, "index.html")
            if os.path.exists(index_path):
                webbrowser.open(f"file://{index_path}")
                self.app.log.info(f"Opened report HTML in browser: {index_path}")
            else:
                self.app.log.error(f"Report HTML not found: {index_path}")
        
        except Exception as e:
            self.app.log.error(f"Error viewing report HTML: {e}")
    
    def view_report_pdf(self) -> None:
        """Open the selected report PDF in a browser."""
        if not self.selected_report:
            return
        
        try:
            # Same process as view_report_html but for PDF
            session_hash = get_current_session()
            if not session_hash:
                self.app.log.error("No active session found")
                return
            
            session_dir = get_session_dir(session_hash)
            reports_dir = os.path.join(session_dir, "reports")
            
            report_dir = None
            report_id = self.selected_report.get("report_id")
            
            for dir_name in os.listdir(reports_dir):
                if dir_name.startswith("hash"):
                    meta_path = os.path.join(reports_dir, dir_name, "meta.json")
                    if os.path.exists(meta_path):
                        with open(meta_path, 'r') as f:
                            meta = json.load(f)
                            if meta.get("report_id") == report_id:
                                report_dir = os.path.join(reports_dir, dir_name)
                                break
            
            if not report_dir:
                self.app.log.error(f"Report directory not found for report ID: {report_id}")
                return
            
            # Look for a summary.pdf or verify.pdf file (main reports)
            for filename in ["summary.pdf", "verify.pdf", "index.pdf"]:
                pdf_path = os.path.join(report_dir, filename)
                if os.path.exists(pdf_path):
                    webbrowser.open(f"file://{pdf_path}")
                    self.app.log.info(f"Opened report PDF in browser: {pdf_path}")
                    return
            
            self.app.log.error("No report PDF found")
        
        except Exception as e:
            self.app.log.error(f"Error viewing report PDF: {e}")
    
    def rerun_report(self) -> None:
        """Rerun the selected report."""
        if not self.selected_report:
            return
        
        try:
            report_id = self.selected_report.get("report_id")
            self.app.log.info(f"Rerunning report: {report_id}")
            
            result = run_command("report_rerun", report_id=report_id)
            
            if result.get("status") == "fresh":
                self.app.log.info(f"Report {report_id} is still fresh, no need to regenerate")
            else:
                new_report_id = result.get("report_id")
                self.app.log.info(f"Report {report_id} regenerated with new ID: {new_report_id}")
            
            # Refresh the reports list
            self.load_reports()
        
        except Exception as e:
            self.app.log.error(f"Error rerunning report: {e}")


# --- Main Application ---

class TUIApplication(App[None]):
    """The main Textual application."""

    CSS = CSS
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+l", "clear_log", "Clear Log"),
        ("r", "show_reports", "Reports"),
    ]
    TITLE = "Document Processing System"

    # Reactive properties to update UI elements
    selected_command_name = reactive[Optional[str]](None)
    session_hash = reactive[Optional[str]](None)
    session_dir = reactive[Optional[str]](None)
    config_env = reactive[str]("dev")  # Default env
    system_os = reactive[str]("windows")  # Default OS

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="app-grid"):
            yield ListView(id="commands-list")
            yield VerticalScroll(Static("Select a command", id="details-panel"))
            yield Log(id="log-panel", highlight=True)
        yield Footer()

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        self.setup_logging()
        self.load_commands()
        self.load_status()
        self.query_one(ListView).focus()
        self.log.info("TUI Application Started. Select a command or press 'r' to access Reports.")

    def setup_logging(self) -> None:
        """Configure logging to output to the Log widget."""
        log_widget = self.query_one(Log)
        self.log_handler = TuiHandler(log_widget)

        # Configure the root logger (or your specific app logger)
        root_logger = logging.getLogger()
        root_logger.addHandler(self.log_handler)
        root_logger.setLevel(logging.INFO)
        self.log.info("Logging configured for TUI.")

    def load_commands(self) -> None:
        """Load commands from commands.py into the ListView."""
        list_view = self.query_one(ListView)
        try:
            commands_dict = list_commands()
            # Ensure 'all' command is included if not explicitly defined with 'func'
            if 'all' not in commands_dict:
                commands_dict['all'] = {
                    "description": "Run all steps: import, validate, map, html, pdf.",
                    "args": ["file_path"]  # Assume 'all' needs file_path like 'import'
                }
            elif "args" not in commands_dict['all']:
                commands_dict['all']["args"] = ["file_path"]

            for name, info in commands_dict.items():
                list_view.append(CommandItem(name, info))
            self.log.info(f"Loaded {len(commands_dict)} commands.")
        except Exception as e:
            self.log.error(f"Failed to load commands: {e}")
            self.query_one("#details-panel").update(f"[red]Error loading commands:\n{e}[/red]")

    def load_status(self) -> None:
        """Load current session status and config info."""
        try:
            self.session_hash = get_current_session()
            if self.session_hash:
                self.session_dir = get_session_dir(self.session_hash)
            else:
                self.session_dir = None

            self.config_env = os.getenv("ENV", "dev")
            self.system_os = os.getenv("SYSTEM_OS", "windows").lower()  # Standardize to lowercase
            self.update_details_panel()
        except FileNotFoundError:
            self.session_hash = None
            self.session_dir = None
            self.log.warning(f"{STATUS_FILE} not found. No active session.")
        except Exception as e:
            self.log.error(f"Error loading status/config: {e}")
            self.session_hash = None
            self.session_dir = None

    def update_details_panel(self) -> None:
        """Update the details panel based on selected command and session status."""
        details_panel = self.query_one("#details-panel")
        content = Text()

        # --- Session Info ---
        content.append("Session Status\n", style="bold underline")
        content.append(f" Environment: {self.config_env}\n")
        if self.session_hash:
            content.append(f" Session Hash: {self.session_hash[:12]}...\n")
            content.append(f" Session Dir: {Path(self.session_dir).name if self.session_dir else 'N/A'}\n")
        else:
            content.append(" Session Hash: [dim]None (Import a file first)[/dim]\n")
            content.append(" Session Dir: [dim]N/A[/dim]\n")

        content.append("\n")  # Separator

        # --- Command Info ---
        if self.selected_command_name:
            try:
                commands_dict = list_commands()
                if 'all' not in commands_dict:
                    commands_dict['all'] = {"description": "Run all steps...", "args": ["file_path"]}
                elif "args" not in commands_dict.get('all', {}):
                    commands_dict['all']["args"] = ["file_path"]

                command_info = commands_dict.get(self.selected_command_name)

                if command_info:
                    content.append(f"Command: {self.selected_command_name.capitalize()}\n", style="bold underline")
                    content.append(f" Description: {command_info.get('description', 'No description available.')}\n")
                    args = command_info.get("args", [])
                    if args:
                        content.append(f" Arguments Needed: {', '.join(args)}\n")
                    else:
                        content.append(" Arguments Needed: None\n")
                    content.append("\nPress [bold]Enter[/bold] to run.")
                else:
                    content.append(f"[red]Error: Command '{self.selected_command_name}' not found in registry.[/red]\n")
            except Exception as e:
                content.append(f"[red]Error loading command details: {e}[/red]\n")
        else:
            content.append("Select a command from the left panel.", style="dim")

        details_panel.update(content)

    # --- Event Handlers ---

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        """Handle command selection."""
        if isinstance(event.item, CommandItem):
            self.selected_command_name = event.item.command_name
            self.update_details_panel()

    def on_key(self, event: "events.Key") -> None:
        # Skip global key handling if a modal screen is active
        if self.screen and isinstance(self.screen, ModalScreen):
            return

        # Get the first ListView widget, or None if not present
        list_view = next(iter(self.query(ListView)), None)
        if list_view and list_view.has_focus and event.key == "enter":
            if self.selected_command_name:
                self.action_run_command()
            else:
                self.log.warning("No command selected.")
                self.app.bell()

    def on_argument_modal_submitted(self, message: ArgumentModal.Submitted) -> None:
        """Handle arguments submitted from the modal."""
        self.log.info(f"Arguments received for '{message.command_name}': {message.args}")
        self.run_command_worker(message.command_name, message.args)  # Run in background

    # --- Actions ---

    def action_run_command(self) -> None:
        """Initiate running the selected command."""
        if not self.selected_command_name:
            self.log.warning("No command selected to run.")
            self.app.bell()
            return

        command_name = self.selected_command_name
        try:
            commands_dict = list_commands()
            if 'all' not in commands_dict:
                commands_dict['all'] = {"description": "Run all steps...", "args": ["file_path"]}
            elif "args" not in commands_dict.get('all', {}):
                commands_dict['all']["args"] = ["file_path"]

            command_info = commands_dict.get(command_name)

            if not command_info:
                self.log.error(f"Command '{command_name}' not found in registry during run attempt.")
                return

            required_args = command_info.get("args", [])

            if command_name not in ["import", "all"] and not self.session_hash:
                self.log.error(f"Command '{command_name}' requires an active session. Import a file first.")
                self.app.bell()
                return

            if required_args:
                self.log.info(f"Command '{command_name}' requires arguments: {required_args}. Showing modal.")
                self.push_screen(ArgumentModal(command_name, required_args))
            else:
                self.log.info(f"Running command '{command_name}' (no arguments needed).")
                self.run_command_worker(command_name, {})  # Run in background

        except Exception as e:
            self.log.error(f"Error preparing command '{command_name}': {e}")

    def run_command_worker(self, command_name: str, args: Dict[str, Any]) -> None:
        """Runs the command in a background worker thread."""
        self.log.info(f"[yellow]Executing '{command_name}' with args: {args}...[/]")
        details_panel = self.query_one("#details-panel")
        # Save current details so we can append if needed
        original_content = details_panel.renderable
        details_panel.update(f"[yellow]Running {command_name}...[/]")

        def _run() -> None:
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            success = False
            result_data = None
            error_msg = None

            try:
                result_data = run_command(command_name, **args)
                success = True
            except FileNotFoundError as e:
                error_msg = f"File not found: {e}"
                self.log.error(f"[red]Error running '{command_name}': {error_msg}[/red]")
            except ValueError as e:
                error_msg = str(e)
                self.log.error(f"[red]Error running '{command_name}': {error_msg}[/red]")
            except Exception as e:
                import traceback
                error_msg = f"Unexpected error: {e}\n{traceback.format_exc()}"
                self.log.error(f"[red]Failed to run command '{command_name}': {error_msg}[/red]")

            self.call_from_thread(self.on_worker_complete, success, command_name, result_data, error_msg, original_content)

        self.run_worker(_run, thread=True, exclusive=True, group=f"cmd_{command_name}")

    def on_worker_complete(self, success: bool, command_name: str, result: Any, error: Optional[str], original_details: RenderableType) -> None:
        """Called when the background worker finishes."""
        details_panel = self.query_one("#details-panel")

        if success:
            self.log.info(f"[green]{CHECK_MARK} Command '{command_name}' completed successfully.[/green]")
            message = f"[green]{CHECK_MARK} {command_name} finished successfully.[/green]\n"
            if isinstance(result, dict):
                if command_name == 'import' and 'hash' in result:
                    message += f"Session Hash: {result['hash']}\nOutput Dir: {result.get('session_dir', 'N/A')}\n"
                elif 'num_files' in result:
                    message += f"Generated {result['num_files']} files.\n"
            if isinstance(original_details, Text):
                message += original_details.plain
            else:
                message += str(original_details)
            details_panel.update(message)
        else:
            self.log.error(f"[red]✗ Command '{command_name}' failed.[/red]")
            error_line = error.splitlines()[0] if error else "Unknown"
            message = f"[red]✗ {command_name} failed.[/red]\nError: {error_line}\nSee logs below.\n\n"
            if isinstance(original_details, Text):
                message += original_details.plain
            else:
                message += str(original_details)
            details_panel.update(message)

        self.query_one(ListView).focus()  # Return focus to command list

    def action_clear_log(self) -> None:
        """Clears the log panel."""
        log_widget = self.query_one(Log)
        log_widget.clear()
        self.log.info("Log cleared.")

    def action_toggle_dark(self) -> None:
        """Toggle dark mode."""
        self.dark = not self.dark

    def action_show_reports(self) -> None:
        """Show the reports screen."""
        self.push_screen(ReportsScreen())


if __name__ == "__main__":
    try:
        config = load_config()
        output_path = config.get("storage", {}).get("path", "output")
        os.makedirs(output_path, exist_ok=True)
    except Exception as e:
        print(f"Warning: Could not ensure output directory '{output_path}' exists: {e}")

    app = TUIApplication()
    app.run()
