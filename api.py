#!/usr/bin/env python
"""
REST API for the Document Processing System using FastAPI.
"""

import os
import sys
import json
import logging
import tempfile
import shutil
import traceback
import zipfile
from io import BytesIO
from typing import Dict, List, Any, Optional
from pathlib import Path
from urllib.parse import quote, unquote
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Form, Body, Header, APIRouter, Request
from fastapi.responses import JSONResponse, HTMLResponse, FileResponse, StreamingResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Import project modules
from commands import COMMANDS, run_command, list_commands
from core.session import get_current_session, get_session_dir, load_config, OUTPUT_DIR
from core.auth.api_auth_endpoints import auth_router
from core.helpers.helper_endpoints import helper_router
from core.logs.logs_api import logs_router

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("docproc_api")

# Helper function to load status information
def load_status() -> Dict[str, Any]:
    """Load the current status information of the application."""
    try:
        session_hash = get_current_session()
        if not session_hash:
            return {"active_session": False}

        session_dir = Path(get_session_dir(session_hash))
        status_file = session_dir / "status.json"

        if not status_file.exists():
            return {"active_session": True, "session_hash": session_hash, "current_state": {}}

        with open(status_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading status: {e}", exc_info=True)
        return {"active_session": False, "error": str(e)}

# --- Custom StaticFiles for SPA ---
class SPAStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope):
        response = await super().get_response(path, scope)
        # If file not found and it's likely a client-side route (no extension), serve index.html
        if response.status_code == 404 and "." not in path.split('/')[-1]: # Check only last part for extension
            logger.debug(f"SPAStaticFiles: Path '{path}' not found, serving index.html for SPA routing.")
            try:
                return await super().get_response("index.html", scope)
            except Exception as e:
                 logger.error(f"SPAStaticFiles: Error serving index.html: {e}")
                 # Fallback to a generic 404 if index.html itself fails
                 return response # Return original 404
        return response

# --- Setup Static Files Dynamically ---
def setup_static_files_and_routes(app: FastAPI):
    """
    Sets up static file mounts based *dynamically* on the api.static_mounts config.
    """
    mounted_paths = {} # Track {url_path: filesystem_path} to prevent overlap

    try:
        config = load_config()
        api_config = config.get("api", {})
        static_mounts_config = api_config.get("static_mounts", {})
        logger.info(f"Loaded static_mounts config: {static_mounts_config}")

        # --- Mount Dashboard (SPA) ---
        dashboard_endpoint = static_mounts_config.get("dashboard", "/") # Usually "/"
        dashboard_dir_relative = static_mounts_config.get("dashboard_dir", "public/dist")
        dashboard_dir_abs = Path(dashboard_dir_relative).resolve()

        if dashboard_dir_abs.exists() and dashboard_dir_abs.is_dir():
            logger.info(f"Mounting Dashboard SPA from '{dashboard_dir_abs}' at '{dashboard_endpoint}'")
            # Use SPAStaticFiles for SPA routing (handles index.html fallback)
            app.mount(dashboard_endpoint, SPAStaticFiles(directory=str(dashboard_dir_abs), html=True), name="dashboard_spa")
            mounted_paths[dashboard_endpoint] = dashboard_dir_abs
        else:
            logger.warning(f"Dashboard directory not found, skipping mount: {dashboard_dir_abs}")

        # --- Mount other configured static paths (/static, /logs) ---
        # Prioritize more specific mounts like /static or /logs before the root dashboard
        mount_order = ["session", "logs"] # Process these potential mounts first
        for mount_name in mount_order:
             endpoint_path = static_mounts_config.get(mount_name) # e.g., /static or /logs
             dir_key = f"{mount_name}_dir" # e.g., session_dir or logs_dir
             path_from_config = static_mounts_config.get(dir_key)

             if not endpoint_path or not path_from_config:
                 logger.debug(f"Config missing endpoint ('{mount_name}') or directory ('{dir_key}') definition. Skipping.")
                 continue

             # Resolve filesystem path (handle relative/absolute)
             fs_path = Path(path_from_config)
             if not fs_path.is_absolute():
                  fs_path = Path.cwd() / fs_path # Assume relative to project root
             fs_path_abs = fs_path.resolve()

             # Check for overlap with already mounted paths
             already_mounted_at = None
             for mounted_endpoint, mounted_fs_path in mounted_paths.items():
                 # Check if the new path is within an existing mounted path OR vice versa
                 # Or if they point to the exact same directory
                 if (fs_path_abs == mounted_fs_path or
                     fs_path_abs in mounted_fs_path.parents or
                     mounted_fs_path in fs_path_abs.parents):
                      # More complex check needed if paths partially overlap (e.g. /static/a and /static/a/b)
                      # For simple cases, check exact match or parent/child relationship.
                      # If they are the same directory, check if the endpoint is different.
                      if fs_path_abs == mounted_fs_path and mounted_endpoint != endpoint_path:
                          already_mounted_at = mounted_endpoint
                          break
                      # Basic check if one is inside the other - might need refinement
                      elif mounted_endpoint != endpoint_path:
                           # Basic parent/child overlap check - might not cover all cases perfectly
                           if str(fs_path_abs).startswith(str(mounted_fs_path)) or \
                              str(mounted_fs_path).startswith(str(fs_path_abs)):
                                logger.warning(f"Potential overlap: Trying to mount '{endpoint_path}' ({fs_path_abs}) which might overlap with existing mount '{mounted_endpoint}' ({mounted_fs_path})")
                                # Decide how to handle overlap - maybe skip, maybe allow if specific enough
                                # For now, let's skip if it's the same base path:
                                if fs_path_abs == mounted_fs_path:
                                     already_mounted_at = mounted_endpoint
                                     break


             if already_mounted_at:
                  logger.warning(f"Skipping mount for '{endpoint_path}' because the directory '{fs_path_abs}' is already effectively mounted at '{already_mounted_at}'.")
                  continue

             # Check if directory exists and mount
             if fs_path_abs.exists() and fs_path_abs.is_dir():
                 logger.info(f"Mounting static files from '{fs_path_abs}' at '{endpoint_path}' (name: {mount_name})")
                 # Use standard StaticFiles for these non-SPA mounts
                 app.mount(endpoint_path, StaticFiles(directory=str(fs_path_abs)), name=mount_name)
                 mounted_paths[endpoint_path] = fs_path_abs # Track it
             else:
                 logger.warning(f"Directory for endpoint '{endpoint_path}' not found or not a directory, skipping mount: {fs_path_abs}")


    except FileNotFoundError as e:
         logger.error(f"Configuration Error during static mount setup: {e}")
    except Exception as e:
        logger.error(f"Error setting up static file mounts: {e}", exc_info=True)
        traceback.print_exc()

# --- Lifespan Manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Code to run on startup
    logger.info("FastAPI application starting up...")
    yield
    # Code to run on shutdown
    logger.info("FastAPI application shutting down...")

# --- Create FastAPI App ---
app = FastAPI(
    title="Document Processing API",
    description="API for processing CSV/Excel files into HTML/PDF documents",
    version="1.0.0",
    lifespan=lifespan
)

# --- React App Direct Routes (Serve index.html for /app/*) ---
@app.get("/app", include_in_schema=False)
@app.get("/app/{rest_of_path:path}", include_in_schema=False)
async def serve_react_app(rest_of_path: str = ""):
    logger.info(f"Serving React app index.html for path: /app/{rest_of_path}")
    dashboard_dir = Path("public/dist").resolve()
    index_path = dashboard_dir / "index.html"
    if not index_path.exists():
        logger.error(f"React app index.html not found at {index_path}")
        raise HTTPException(status_code=404, detail="React app index not found. Build the frontend.")
    try:
        with open(index_path, "r", encoding='utf-8') as f:
            content = f.read()
        return HTMLResponse(content=content)
    except Exception as e:
         logger.error(f"Error reading React index.html: {e}", exc_info=True)
         raise HTTPException(status_code=500, detail="Could not load application UI.")

# --- API Routers ---
main_router = APIRouter()

# Pydantic models
class CommandResponse(BaseModel):
    success: bool
    command: str
    result: Dict[str, Any] = {}
    error: Optional[str] = None

class ImportRequest(BaseModel):
    file_path: str

class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None

# --- API Endpoint Implementations ---

@main_router.get("/status", response_model=Dict[str, Any])
async def get_status():
    """Get current session status."""
    session_hash = get_current_session()
    status_data = load_status() # Load full status

    if not session_hash or not status_data.get("active_session"):
        return {
            "active_session": False,
            "session_hash": None,
            "document_type": None,
            "last_operation": None
        }

    # Return relevant parts of the status
    return {
        "active_session": True,
        "session_hash": session_hash,
        "document_type": status_data.get("current_state", {}).get("document_type"),
        "last_operation": status_data.get("current_state", {}).get("last_operation")
    }


@main_router.post("/sessions/{session_hash}/activate", response_model=CommandResponse)
async def activate_session_endpoint(session_hash: str):
    """Activate a specific session by hash."""
    try:
        result_dict = run_command("activate_session", session_hash=session_hash)
        return CommandResponse(
            success=True,
            command="activate_session",
            result=result_dict # Pass the whole result dict from the command
        )
    except ValueError as ve:
         logger.error(f"Activation failed for session {session_hash}: {ve}")
         raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        logger.error(f"Error activating session {session_hash}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error during activation: {str(e)}")

@main_router.get("/commands", response_model=Dict[str, Dict[str, Any]])
async def get_commands():
    """List all available commands."""
    return list_commands()

# Helper to check API auth from config
def _check_api_auth(api_key: Optional[str]) -> bool:
    try:
        config = load_config()
        api_config = config.get("api", {})
        if not api_config.get("auth_enabled", False):
            return True # Auth disabled
        valid_key = api_config.get("auth_token")
        if not valid_key:
            return True # No key configured
        return api_key == valid_key
    except FileNotFoundError:
        logger.warning("Config file not found when checking API auth, defaulting to no auth")
        return True # Default to allow if config fails
    except Exception as e:
        logger.error(f"Error checking API auth: {e}")
        return False # Default to deny on other errors

@main_router.post("/run/import", response_model=CommandResponse)
async def run_import(file_path: str = Form(...), api_key: str = Header(None, alias="X-API-Key")):
    """Run import command with a file path."""
    if not _check_api_auth(api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    if not os.path.isfile(file_path): # Use os.path
        raise HTTPException(status_code=400, detail=f"File not found: {file_path}")
    try:
        result = run_command("import", file_path=file_path)
        return CommandResponse(success=True, command="import", result=result)
    except Exception as e:
        logger.error(f"Error running import command: {e}", exc_info=True)
        return CommandResponse(success=False, command="import", error=str(e))

@main_router.post("/run/import-upload", response_model=CommandResponse)
async def run_import_upload(file: UploadFile = File(...), api_key: str = Header(None, alias="X-API-Key")):
    """Run import command with an uploaded file."""
    if not _check_api_auth(api_key):
         raise HTTPException(status_code=401, detail="Invalid or missing API key")

    temp_dir = None # Initialize outside try
    try:
        temp_dir = tempfile.mkdtemp()
        temp_file_path = Path(temp_dir) / file.filename
        logger.info(f"Saving uploaded file to temporary path: {temp_file_path}")

        # Use shutil.copyfileobj for potentially large files
        with open(temp_file_path, "wb") as f_dest:
             shutil.copyfileobj(file.file, f_dest)
        logger.info(f"Saved uploaded file {file.filename} ({file.size} bytes)")


        result = run_command("import", file_path=str(temp_file_path)) # Pass path as string
        logger.info(f"Import command completed for uploaded file.")
        return CommandResponse(success=True, command="import", result=result)

    except Exception as e:
        logger.error(f"Error running import-upload command: {e}", exc_info=True)
        return CommandResponse(success=False, command="import-upload", error=f"Upload/Import failed: {str(e)}")
    finally:
        # Ensure cleanup happens
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
                logger.info(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as cleanup_e:
                 logger.error(f"Error cleaning up temp directory {temp_dir}: {cleanup_e}")
        # Close the uploaded file object
        await file.close()


@main_router.post("/run/map", response_model=CommandResponse)
async def run_map_command(args: Dict[str, Any] = Body({}), api_key: str = Header(None, alias="X-API-Key")):
    """Endpoint for map command (generation or update)."""
    if not _check_api_auth(api_key):
         raise HTTPException(status_code=401, detail="Invalid or missing API key")
    try:
        if "field_updates" in args:
            logger.info("Detected mapping update request")
            result = run_command("update_mapping", field_updates=args.get("field_updates", {}))
            return CommandResponse(success=True, command="update_mapping", result=result)
        else:
            logger.info("Generating new mapping")
            result = run_command("map")
            return CommandResponse(success=True, command="map", result=result)
    except Exception as e:
        logger.error(f"Error in mapping operation: {e}", exc_info=True)
        return CommandResponse(success=False, command="map", error=str(e))

# Generic command runner (should come after specific handlers like /run/map)
@main_router.post("/run/{command}", response_model=CommandResponse)
async def run_api_command(command: str, args: Dict[str, Any] = Body({}), api_key: str = Header(None, alias="X-API-Key")):
    """Generic endpoint to run any command."""
    if not _check_api_auth(api_key):
         raise HTTPException(status_code=401, detail="Invalid or missing API key")

    # Map command handled separately above
    if command == "map":
         # This case should ideally not be hit if /run/map is defined first,
         # but as a fallback, redirect or call the specific handler.
         # Let's call the specific handler to avoid redirection complexity client-side.
         logger.warning(f"Generic /run/{command} called for 'map', using specific handler.")
         return await run_map_command(args, api_key) # Pass api_key if needed by map command logic

    if command not in COMMANDS and command != "all": # Check if command is valid
        raise HTTPException(status_code=404, detail=f"Command '{command}' not found")

    try:
        # Pass arguments correctly
        result = run_command(command, **args)
        return CommandResponse(success=True, command=command, result=result)
    except Exception as e:
        logger.error(f"Error running command '{command}': {e}", exc_info=True)
        return CommandResponse(success=False, command=command, error=str(e))


# --- Report endpoints ---
@main_router.post("/report/generate", response_model=CommandResponse)
async def api_report_generate(api_key: str = Header(None, alias="X-API-Key")):
    """Generate all reports for the current session."""
    if not _check_api_auth(api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    try:
        result = run_command("report_generate")
        return CommandResponse(success=True, command="report_generate", result=result)
    except Exception as e:
        logger.error(f"Error generating reports: {e}", exc_info=True)
        return CommandResponse(success=False, command="report_generate", error=str(e))

@main_router.post("/report/rerun", response_model=CommandResponse)
async def api_report_rerun(report_id: str = Body(..., embed=True), api_key: str = Header(None, alias="X-API-Key")):
    """Re-run a previously generated report."""
    if not _check_api_auth(api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    try:
        result = run_command("report_rerun", report_id=report_id)
        return CommandResponse(success=True, command="report_rerun", result=result)
    except Exception as e:
        logger.error(f"Error re-running report '{report_id}': {e}", exc_info=True)
        return CommandResponse(success=False, command="report_rerun", error=str(e))

@main_router.get("/report/list", response_model=CommandResponse)
async def api_report_list(api_key: str = Header(None, alias="X-API-Key")):
    """List all report runs with their status."""
    if not _check_api_auth(api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    try:
        reports = run_command("report_list")
        return CommandResponse(success=True, command="report_list", result={"reports": reports})
    except Exception as e:
        logger.error(f"Error listing reports: {e}", exc_info=True)
        return CommandResponse(success=False, command="report_list", error=str(e))

# Helper function to find report path (used by report file endpoints)
def _find_report_dir(report_id: str) -> Optional[Path]:
    """Finds the directory for a given report ID."""
    session_hash = get_current_session()
    if not session_hash: return None
    session_dir = Path(get_session_dir(session_hash))
    reports_parent_dir = session_dir / "reports"
    if not reports_parent_dir.is_dir(): return None

    for potential_dir in reports_parent_dir.iterdir():
        if potential_dir.is_dir() and potential_dir.name.startswith("hash"):
            meta_path = potential_dir / "meta.json"
            if meta_path.exists():
                try:
                    with open(meta_path, 'r') as f:
                        meta = json.load(f)
                    if meta.get("report_id") == report_id:
                        return potential_dir
                except Exception:
                    continue # Ignore errors reading meta.json
    return None

@main_router.get("/report/{report_id}/html/{filename}")
async def get_report_html(report_id: str, filename: str, api_key: str = Header(None, alias="X-API-Key")):
    """Serve an HTML report file."""
    if not _check_api_auth(api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    report_dir = _find_report_dir(report_id)
    if not report_dir:
        raise HTTPException(status_code=404, detail=f"Report directory for ID {report_id} not found.")

    html_path = report_dir / filename
    if not html_path.is_file():
        raise HTTPException(status_code=404, detail=f"HTML file {filename} not found in report {report_id}.")

    return FileResponse(html_path, media_type="text/html")

@main_router.get("/report/{report_id}/pdf/{filename}")
async def get_report_pdf(report_id: str, filename: str, api_key: str = Header(None, alias="X-API-Key")):
    """Serve a PDF report file."""
    if not _check_api_auth(api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    report_dir = _find_report_dir(report_id)
    if not report_dir:
        raise HTTPException(status_code=404, detail=f"Report directory for ID {report_id} not found.")

    pdf_path = report_dir / filename
    if not pdf_path.is_file():
        raise HTTPException(status_code=404, detail=f"PDF file {filename} not found in report {report_id}.")

    return FileResponse(pdf_path, media_type="application/pdf")


# --- Direct file serving from output directory ---
# File serving endpoints
@main_router.get("/files/{session_hash}/html/{filename}")
async def serve_html_file(session_hash: str, filename: str):
    """Serve an HTML file directly from the output directory."""
    # Construct the path to the HTML file
    file_path = Path(OUTPUT_DIR) / session_hash / "html" / filename

    # Check if the file exists
    if not file_path.is_file():
        logger.error(f"HTML file not found: {file_path}")
        raise HTTPException(status_code=404, detail=f"HTML file {filename} not found for session {session_hash}")

    # Serve the file
    logger.info(f"Serving HTML file: {file_path}")
    return FileResponse(file_path, media_type="text/html")


@main_router.get("/files/{session_hash}/pdf/{filename}")
async def serve_pdf_file(session_hash: str, filename: str):
    """Serve a PDF file directly from the output directory."""
    # First try the standard PDF directory
    file_path = Path(OUTPUT_DIR) / session_hash / "pdf" / filename

    # If not found, try the www/generate/pdf directory
    if not file_path.is_file():
        www_pdf_path = Path(OUTPUT_DIR) / session_hash / "www" / "generate" / "pdf" / filename
        if www_pdf_path.is_file():
            file_path = www_pdf_path
        else:
            logger.error(f"PDF file not found in either location: {file_path} or {www_pdf_path}")
            raise HTTPException(status_code=404, detail=f"PDF file {filename} not found for session {session_hash}")

    # Serve the file
    logger.info(f"Serving PDF file: {file_path}")
    return FileResponse(file_path, media_type="application/pdf")


@main_router.get("/files/{session_hash}/logs/{filename}")
async def serve_log_file(session_hash: str, filename: str):
    """Serve a log file directly from the output directory."""
    # Construct the path to the log file
    file_path = Path(OUTPUT_DIR) / session_hash / "logs" / filename

    # Check if the file exists
    if not file_path.is_file():
        logger.error(f"Log file not found: {file_path}")
        raise HTTPException(status_code=404, detail=f"Log file {filename} not found for session {session_hash}")

    # Serve the file
    logger.info(f"Serving log file: {file_path}")
    return FileResponse(file_path, media_type="text/plain")


@main_router.get("/files/{session_hash}/www/{filename:path}")
async def serve_www_file(session_hash: str, filename: str):
    """Serve a file from the www directory."""
    # Construct the path to the www file
    file_path = Path(OUTPUT_DIR) / session_hash / "www" / filename

    # Check if the file exists
    if not file_path.is_file():
        logger.error(f"WWW file not found: {file_path}")
        raise HTTPException(status_code=404, detail=f"File {filename} not found in www directory for session {session_hash}")

    # Determine the media type based on the file extension
    media_type = "text/plain"  # Default
    if filename.endswith(".html") or filename.endswith(".htm"):
        media_type = "text/html"
    elif filename.endswith(".css"):
        media_type = "text/css"
    elif filename.endswith(".js"):
        media_type = "application/javascript"
    elif filename.endswith(".json"):
        media_type = "application/json"
    elif filename.endswith(".png"):
        media_type = "image/png"
    elif filename.endswith(".jpg") or filename.endswith(".jpeg"):
        media_type = "image/jpeg"
    elif filename.endswith(".gif"):
        media_type = "image/gif"
    elif filename.endswith(".svg"):
        media_type = "image/svg+xml"
    elif filename.endswith(".pdf"):
        media_type = "application/pdf"

    # Serve the file
    logger.info(f"Serving WWW file: {file_path} as {media_type}")
    return FileResponse(file_path, media_type=media_type)


@main_router.get("/files/{session_hash}/{directory}")
async def list_directory_files(session_hash: str, directory: str):
    """List files in a directory for a session."""
    # Construct the path to the directory
    dir_path = Path(OUTPUT_DIR) / session_hash / directory

    # Check if the directory exists
    if not dir_path.is_dir():
        logger.error(f"Directory not found: {dir_path}")
        raise HTTPException(status_code=404, detail=f"Directory {directory} not found for session {session_hash}")

    # Get all files in the directory
    files = []
    for file_path in dir_path.iterdir():
        if file_path.is_file():
            files.append({
                "name": file_path.name,
                "size": file_path.stat().st_size,
                "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat(),
                "url": f"/api/files/{session_hash}/{directory}/{file_path.name}"
            })

    # Sort files by name
    files.sort(key=lambda x: x["name"])

    return {
        "session_hash": session_hash,
        "directory": directory,
        "files": files
    }


@main_router.get("/files/{session_hash}")
async def list_session_directories(session_hash: str):
    """List all directories for a session."""
    # Construct the path to the session directory
    session_dir = Path(OUTPUT_DIR) / session_hash

    # Check if the directory exists
    if not session_dir.is_dir():
        logger.error(f"Session directory not found: {session_dir}")
        raise HTTPException(status_code=404, detail=f"Session {session_hash} not found")

    # Get all directories in the session directory
    directories = []
    for dir_path in session_dir.iterdir():
        if dir_path.is_dir():
            directories.append({
                "name": dir_path.name,
                "url": f"/api/files/{session_hash}/{dir_path.name}"
            })

    # Sort directories by name
    directories.sort(key=lambda x: x["name"])

    return {
        "session_hash": session_hash,
        "directories": directories
    }


@main_router.get("/files/{session_hash}/zip")
async def serve_session_zip(session_hash: str):
    """Create and serve a ZIP file of all files in the session directory."""
    import zipfile
    from io import BytesIO

    # Construct the path to the session directory
    session_dir = Path(OUTPUT_DIR) / session_hash

    # Check if the directory exists
    if not session_dir.is_dir():
        logger.error(f"Session directory not found: {session_dir}")
        raise HTTPException(status_code=404, detail=f"Session {session_hash} not found")

    # Create a BytesIO object to store the ZIP file
    zip_buffer = BytesIO()

    # Create a ZIP file
    with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        # Walk through the session directory and add all files to the ZIP
        for root, _, files in os.walk(session_dir):
            for file in files:
                file_path = os.path.join(root, file)
                # Add the file to the ZIP with a relative path
                arcname = os.path.relpath(file_path, session_dir)
                zip_file.write(file_path, arcname)

    # Reset the buffer position to the beginning
    zip_buffer.seek(0)

    # Serve the ZIP file
    logger.info(f"Serving ZIP file for session: {session_hash}")
    return StreamingResponse(
        zip_buffer,
        media_type="application/zip",
        headers={"Content-Disposition": f"attachment; filename=session_{session_hash}.zip"}
    )


# --- Backward compatibility for /static URLs ---
@main_router.get("/static/{session_hash}/html/{filename}")
async def serve_html_file_static(session_hash: str, filename: str):
    """Backward compatibility for /static URLs."""
    return await serve_html_file(session_hash, filename)


@main_router.get("/static/{session_hash}/pdf/{filename}")
async def serve_pdf_file_static(session_hash: str, filename: str):
    """Backward compatibility for /static URLs."""
    return await serve_pdf_file(session_hash, filename)


@main_router.get("/static/{session_hash}/logs/{filename}")
async def serve_log_file_static(session_hash: str, filename: str):
    """Backward compatibility for /static URLs."""
    return await serve_log_file(session_hash, filename)


@main_router.get("/static/{session_hash}/zip")
async def serve_session_zip_static(session_hash: str):
    """Backward compatibility for /static URLs."""
    return await serve_session_zip(session_hash)

# --- Include API Routers ---
app.include_router(auth_router, prefix="/api")
app.include_router(helper_router, prefix="/api")
app.include_router(logs_router, prefix="/api")
app.include_router(main_router, prefix="/api") # Include your main API routes

# --- Setup Static File Mounts (Reads config) ---
setup_static_files_and_routes(app)

# --- Directory Listing / File Serving Catch-All Route (MUST BE LAST ROUTE) ---
@app.get("/{full_path:path}", include_in_schema=False)
async def serve_static_or_directory(request: Request, full_path: str):
    """
    Fallback route: Serves files from OUTPUT_DIR or directory listings if enabled.
    This handles requests not matched by API routes or specific StaticFiles mounts.
    """

    try:
        config = load_config()
        api_config = config.get("api", {})
        allow_listing = api_config.get("directory_listings", False)

        decoded_path_str = unquote(full_path).strip('/')
        base_serve_dir = Path(OUTPUT_DIR).resolve()

        # Construct path: handle empty path for root listing
        requested_fs_path = base_serve_dir if not decoded_path_str else (base_serve_dir / decoded_path_str).resolve()

        logger.info(f"--- Catch-All Request Details ---")
        logger.info(f"  URL Path         : /{full_path}")
        logger.info(f"  Decoded Path     : {decoded_path_str}")
        logger.info(f"  Base Serve Dir   : {base_serve_dir}")
        logger.info(f"  Requested FS Path: {requested_fs_path}")

        # Check if path exists
        exists = requested_fs_path.exists()
        logger.info(f"  FS Path Exists?  : {exists}")

        is_file = requested_fs_path.is_file() if exists else False
        is_dir = requested_fs_path.is_dir() if exists else False
        logger.info(f"  Is File?         : {is_file}")
        logger.info(f"  Is Dir?          : {is_dir}")
        logger.info(f"  Listing Enabled? : {allow_listing}")
        logger.info(f"---------------------------------")

        # Security Check
        is_within_base = requested_fs_path == base_serve_dir or base_serve_dir in requested_fs_path.parents
        if not is_within_base:
            logger.error(f"Access Denied (Path Traversal): '{decoded_path_str}' resolved outside base '{base_serve_dir}'")
            raise HTTPException(status_code=404, detail="Not Found (Restricted Path)")

        if not exists:
            logger.warning(f"Path Not Found on Filesystem: {requested_fs_path}")
            raise HTTPException(status_code=404, detail="Not Found (Path does not exist)")

        # Serve File
        if is_file:
            logger.info(f"Serving file via FileResponse: {requested_fs_path}")
            return FileResponse(requested_fs_path)

        # Serve Directory Listing
        if is_dir:
            if not allow_listing:
                logger.warning(f"Directory Listing Disabled - Access Denied: {requested_fs_path}")
                raise HTTPException(status_code=404, detail="Not Found (Listing Disabled)")

            logger.info(f"Generating directory listing for: {requested_fs_path}")
            try:
                items = sorted(list(requested_fs_path.iterdir()), key=lambda x: (not x.is_dir(), x.name.lower()))
            except OSError as e:
                logger.error(f"Error listing directory {requested_fs_path}: {e}", exc_info=True)
                raise HTTPException(status_code=500, detail="Cannot read directory contents.")

            # Build HTML
            path_from_web_root = decoded_path_str

            html_content = f"""<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><title>Index of /{path_from_web_root}</title>
                           <style>body{{font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif; padding: 15px; font-size: 0.95rem;}} ul{{list-style: none; padding-left: 0;}} li{{margin-bottom: 6px; display: flex; align-items: center; border-bottom: 1px solid #eee; padding-bottom: 6px;}} a{{text-decoration: none; color: #0056b3; margin-left: 8px;}} a:hover{{text-decoration: underline;}} .icon{{display: inline-block; width: 24px; text-align: center; font-size: 1.1em;}} .details{{font-size: 0.85em; color: #6c757d; margin-left: auto; padding-left: 15px; white-space: nowrap;}}</style>
                           </head><body><h1>Index of /{path_from_web_root}</h1><hr><ul>"""

            if requested_fs_path != base_serve_dir:
                 parent_rel_path_str = str(requested_fs_path.parent.relative_to(base_serve_dir))
                 parent_url_segment = quote(parent_rel_path_str) if parent_rel_path_str != '.' else ''
                 html_content += f'<li><span class="icon">⬆️</span><a href="/{parent_url_segment}">Parent Directory</a></li>'

            for item in items:
                item_rel_path_str = str(item.relative_to(base_serve_dir))
                encoded_url = f"/{quote(item_rel_path_str)}"
                details_html = ""
                try:
                    stat_result = item.stat()
                    size_str = f"{stat_result.st_size:,}" if item.is_file() else "-"
                    mtime_str = datetime.fromtimestamp(stat_result.st_mtime).strftime('%Y-%m-%d %H:%M')
                    details_html = f'<span class="details">{size_str.rjust(15)}    {mtime_str}</span>'
                except Exception: details_html = '<span class="details">Error reading details</span>'

                if item.is_dir(): html_content += f'<li><span class="icon">📁</span><a href="{encoded_url}">{item.name}/</a>{details_html}</li>'
                else: html_content += f'<li><span class="icon">📄</span><a href="{encoded_url}" target="_blank">{item.name}</a>{details_html}</li>'

            html_content += "</ul><hr></body></html>"
            return HTMLResponse(content=html_content)

    except Exception as e:
        logger.error(f"Error in catch-all route handler: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")

# --- Configure CORS ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify allowed origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Run the server if executed directly ---
if __name__ == "__main__":
    import uvicorn
    try:
        config = load_config()
        api_config = config.get("api", {})
        host = api_config.get("host", "0.0.0.0")
        port = api_config.get("port", 8000)
        logger.info(f"Starting API server on {host}:{port}")
        uvicorn.run(app, host=host, port=port, log_level="info")
    except Exception as e:
        logger.error(f"Failed to start API server: {e}", exc_info=True)
        sys.exit(1)
