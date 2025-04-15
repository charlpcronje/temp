#!/usr/bin/env python
"""
Session Management - Handle configuration loading, session state, and output directories.
"""

import os
import json
import logging
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional

import dotenv

# Load environment variables
dotenv.load_dotenv()

# Configure logging
# Consider moving logging setup to a central location if not already done
# logging.basicConfig(level=logging.INFO) # Example basic setup
logger = logging.getLogger(__name__) # Use __name__ for module-specific logger

# Set constants
STATUS_FILE = "status.json"
SESSIONS_FILE = "sessions.json" # Legacy, consider phasing out for metadata.json
CONFIG_DIR = "config"
OUTPUT_DIR = "output"

# Get OS setting, default to platform detection if not set
SYSTEM_OS = os.getenv("SYSTEM_OS", "windows").lower()  # Standardize to lowercase for matching


def load_config() -> Dict[str, Any]:
    """
    Load the appropriate configuration file based on the environment.
    Includes validation of required configuration fields.

    Returns:
        Dict containing configuration settings

    Raises:
        FileNotFoundError: If the config file doesn't exist.
        ValueError, TypeError: If config is invalid or missing fields.
    """
    env = os.getenv("ENV", "dev")
    # Ensure CONFIG_DIR path is correct relative to the project root
    # If this script is in core/, config is likely ../config/
    project_root = Path(__file__).resolve().parent.parent
    config_file = project_root / CONFIG_DIR / f"{env}.json"

    logger.debug(f"Attempting to load config from: {config_file}")

    try:
        if not config_file.exists():
            error_msg = (
                f"Configuration file for environment '{env}' not found at '{config_file}'. "
                f"The ENV environment variable is set to '{env}', but the corresponding "
                f"configuration file does not exist.\n"
                f"Check CWD: {os.getcwd()}\n"
                f"Either:\n"
                f"1. Create the config file at {config_file}\n"
                f"2. Set ENV to a different environment with an existing config file\n"
                f"3. Remove the ENV setting to use the default 'dev' environment"
            )
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)

        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Validate required configuration fields
        required_fields = [
            ("application", dict),
            ("storage", dict),
            # Add other essential top-level keys if needed
            ("api", dict),
        ]

        for field, expected_type in required_fields:
            if field not in config:
                raise ValueError(f"Missing required config field: '{field}' in {config_file}")
            if not isinstance(config[field], expected_type):
                raise TypeError(f"Config field '{field}' should be type {expected_type.__name__}, got {type(config[field]).__name__} in {config_file}")

        logger.info(f"Loaded configuration from {config_file}")
        return config

    except json.JSONDecodeError as e:
        error_msg = f"Error parsing config file {config_file}: {e}. The file exists but contains invalid JSON."
        logger.error(error_msg)
        raise ValueError(error_msg) from e # Re-raise as ValueError for consistent handling
    except FileNotFoundError:
        # Re-raise the specific FileNotFoundError from above
        raise
    except (ValueError, TypeError) as e:
         # Re-raise validation errors
         logger.error(f"Configuration validation failed for {config_file}: {e}")
         raise
    except Exception as e:
        error_msg = f"Unexpected error loading config file {config_file}: {e}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg) from e # Re-raise as a more generic runtime error


def load_status() -> Dict[str, Any]:
    """
    Load the current status from status.json. Returns defaults if not found/invalid.
    Ensures the structure matches expected format.
    """
    default_status = {
        "last_updated": None,
        "active_session": False, # Track if a session is globally active
        "session_hash": None,    # Hash of the globally active session
        "current_state": {       # Detailed state of the active session
            "hash": None,
            "sqlite_db_file": None,
            "output_folder": None,
            "last_updated": None,
            "last_operation": None,
            "imported_file": None,
            "document_type": None
        }
    }
    status_path = Path(STATUS_FILE) # Use Path object

    if not status_path.exists():
        logger.warning(f"{STATUS_FILE} not found, returning default status.")
        return default_status
    try:
        with open(status_path, "r", encoding='utf-8') as f:
            status_data = json.load(f)
            # Basic validation: ensure current_state exists
            if "current_state" not in status_data:
                logger.warning(f"'current_state' missing in {STATUS_FILE}. Merging with defaults.")
                status_data["current_state"] = default_status["current_state"]
            # Merge loaded data with defaults to ensure all keys exist
            merged_status = {**default_status, **status_data}
            merged_status["current_state"] = {**default_status["current_state"], **status_data.get("current_state", {})}
            return merged_status
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Error reading or parsing {STATUS_FILE}: {e}. Returning default status.")
        return default_status


def save_status(status: Dict[str, Any]) -> None:
    """
    Save the status to status.json.
    """
    status_path = Path(STATUS_FILE)
    try:
        with open(status_path, "w", encoding='utf-8') as f:
            json.dump(status, f, indent=2)
        logger.debug(f"Saved status to {status_path}")
    except (IOError, TypeError) as e:
        logger.error(f"Failed to save status to {status_path}: {e}")
        # Consider raising an exception here if saving status is critical
        # raise RuntimeError(f"Failed to save status file: {e}") from e


def get_current_session() -> Optional[str]:
    """
    Get the hash of the current globally active session from status.json.

    Returns:
        Session hash as string or None if no active session
    """
    try:
        status = load_status() # Use the robust load_status
        # Check both top-level and current_state for consistency
        if status.get("active_session") and status.get("session_hash"):
            return status.get("session_hash")
        elif status.get("current_state", {}).get("hash"):
             logger.warning("status.json indicates inactive session but current_state has hash. Returning hash from current_state.")
             return status["current_state"]["hash"]
        else:
             logger.debug("No active session found in status.json")
             return None
    except Exception as e:
         # Catch potential errors during loading, though load_status should handle most
         logger.error(f"Error getting current session from status: {e}", exc_info=True)
         return None


def perform_session_activation(session_hash: str) -> Dict[str, Any]:
    """
    Activates a session by updating the global status.json with data from
    the session's metadata.json. Returns the result including the updated
    global status object.

    Args:
        session_hash: The hash of the session to activate.

    Returns:
        A dictionary containing activation message, the last operation
        read from the session's metadata, and the complete updated global
        status object.

    Raises:
        ValueError: If the session directory or its metadata cannot be found/read.
        RuntimeError: If saving the status fails.
    """
    abs_output_dir = Path(OUTPUT_DIR).resolve() # Use absolute path
    session_dir = abs_output_dir / session_hash
    metadata_path = session_dir / "metadata.json"

    if not session_dir.is_dir():
        logger.error(f"Session directory not found during activation: {session_dir}")
        raise ValueError(f"Session '{session_hash}' directory not found.")

    logger.info(f"Attempting to activate session: {session_hash}")

    # Load session-specific metadata
    session_metadata = {}
    last_operation_from_metadata = None
    document_type_from_metadata = None
    imported_file_from_metadata = None

    if metadata_path.exists():
        try:
            with open(metadata_path, "r", encoding='utf-8') as f:
                session_metadata = json.load(f)
                # Get key session details from its metadata
                document_type_from_metadata = session_metadata.get("document_type")
                last_operation_from_metadata = session_metadata.get("last_operation")
                imported_file_from_metadata = session_metadata.get("imported_file") # Get the original file
                logger.debug(f"Read from {metadata_path} - doc_type: {document_type_from_metadata}, last_op: {last_operation_from_metadata}")
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Error reading or parsing session metadata {metadata_path}: {e}")
            # Continue activation but might lack details
    else:
        logger.warning(f"Metadata file not found for session {session_hash} at {metadata_path}. Activation may lack details.")
        # If metadata is missing, we can't know the last operation for resuming workflow
        # Defaulting might be okay, but it could lead to wrong step.
        # Consider raising an error if metadata is crucial for activation.
        # raise ValueError(f"Metadata file missing for session {session_hash}, cannot activate.")


    # Load current global status (before modification) to update it
    status_to_save = load_status()

    # --- Update the global status.json content ---
    now_iso = datetime.now().isoformat()

    # Update top-level keys
    status_to_save["active_session"] = True
    status_to_save["session_hash"] = session_hash
    status_to_save["last_updated"] = now_iso # When the activation happened

    # Update 'current_state' section with details from the activated session
    current_state = status_to_save.get("current_state", {}) # Get existing or empty dict
    current_state["hash"] = session_hash
    current_state["sqlite_db_file"] = str(session_dir / "data.db") # Use Path object then convert to string
    current_state["output_folder"] = str(session_dir)
    current_state["last_updated"] = now_iso # Reflect activation time

    # Use details read from session metadata
    if document_type_from_metadata:
        current_state["document_type"] = document_type_from_metadata
    if last_operation_from_metadata:
         # This is the crucial part for resuming workflow
         current_state["last_operation"] = last_operation_from_metadata
    elif "last_operation" not in current_state: # Only default if completely missing
         current_state["last_operation"] = "IMPORT_DATA" # Fallback if no history found
    if imported_file_from_metadata: # Restore the original imported file path
         current_state["imported_file"] = imported_file_from_metadata
    # --- End of status update logic ---

    status_to_save["current_state"] = current_state # Put updated state back

    # Save the modified global status to status.json
    try:
        save_status(status_to_save)
        logger.info(f"Session {session_hash} activated. status.json updated.")
    except Exception as e:
         # If saving fails, we should probably signal an error
         logger.error(f"CRITICAL: Failed to save status after activating session {session_hash}: {e}", exc_info=True)
         raise RuntimeError(f"Failed to save status file during activation: {e}") from e

    # IMPORTANT: Return the structure expected by the API endpoint's CommandResponse
    return {
        "message": f"Session {session_hash} activated successfully.",
        # Return the last operation *read from the session's own metadata*
        "last_operation": last_operation_from_metadata, # Frontend uses this to determine the next step
        # Return the *entire saved global status object*
        "status": status_to_save
    }


def update_session_status(session_hash: str, file_path: Optional[str] = None, document_type: Optional[str] = None,
                          operation: str = "IMPORT_DATA") -> Dict[str, Any]:
    """
    Updates status.json (global state) and the specific session's metadata.json
    to reflect the completion of a workflow operation.

    Args:
        session_hash: The hash of the currently active session.
        file_path: Path to the original imported file (usually only set during import).
        document_type: Detected document type (usually only set during validation).
        operation: The name of the operation that just completed (e.g., "VALIDATE_DATA").

    Returns:
        The updated global status dictionary that was saved to status.json.

    Raises:
        RuntimeError: If saving status or metadata fails.
    """
    logger.debug(f"Updating status for session {session_hash}, operation completed: {operation}")
    create_output_dir(session_hash) # Ensure session directories exist

    # --- 1. Update status.json (Global State) ---
    status = load_status() # Load current global status
    now_iso = datetime.now().isoformat()

    # Update top-level status info to reflect this session is now active
    status["last_updated"] = now_iso
    status["active_session"] = True
    status["session_hash"] = session_hash

    # Update the 'current_state' section
    current_state = status.get("current_state", {})
    current_state["hash"] = session_hash
    current_state["last_operation"] = operation # Record the operation JUST COMPLETED
    current_state["last_updated"] = now_iso
    current_state["sqlite_db_file"] = str(Path(OUTPUT_DIR).resolve() / session_hash / "data.db")
    current_state["output_folder"] = str(Path(OUTPUT_DIR).resolve() / session_hash)

    # Conditionally update file path and doc type if provided
    if file_path:
        current_state["imported_file"] = file_path
    if document_type:
        current_state["document_type"] = document_type
    # Ensure keys exist even if not updated now (using get with default)
    current_state.setdefault("imported_file", None)
    current_state.setdefault("document_type", None)

    status["current_state"] = current_state

    # Save the updated global status
    try:
        save_status(status)
        logger.debug("Global status.json updated.")
    except Exception as e:
        logger.error(f"CRITICAL: Failed to save global status during update for op {operation}: {e}", exc_info=True)
        raise RuntimeError(f"Failed to save global status file: {e}") from e


    # --- 2. Update session-specific metadata.json ---
    metadata_path = Path(OUTPUT_DIR).resolve() / session_hash / "metadata.json"
    session_metadata = {}
    if metadata_path.exists():
        try:
            with open(metadata_path, "r", encoding='utf-8') as f:
                session_metadata = json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not read session metadata {metadata_path}: {e}. Will create/overwrite.")

    # Update metadata fields for this specific session
    session_metadata["last_operation"] = operation # Record completed operation here too
    session_metadata["last_updated"] = now_iso # Time of this operation completion
    if document_type:
        session_metadata["document_type"] = document_type
    # Store initial import file path only if it's not already there
    if file_path and "imported_file" not in session_metadata:
        session_metadata["imported_file"] = file_path
    # Set default name and creation timestamp if missing
    session_metadata.setdefault("name", f"Session {session_hash[:8]}")
    session_metadata.setdefault("timestamp", now_iso) # Use current time as creation if missing

    # Save the updated session metadata
    try:
        with open(metadata_path, "w", encoding='utf-8') as f:
            json.dump(session_metadata, f, indent=2)
        logger.debug(f"Session metadata {metadata_path} updated.")
    except (IOError, TypeError) as e:
         logger.error(f"Failed to write session metadata {metadata_path}: {e}", exc_info=True)
         # Depending on severity, you might want to raise an error here too
         # raise RuntimeError(f"Failed to save session metadata: {e}") from e

    # (Optional: Update legacy sessions.json - consider removing this later)
    # update_session_data(session_hash, operation, document_type)

    logger.info(f"Session status & metadata updated for hash={session_hash}, operation={operation}")
    return status # Return the updated global status


def create_output_dir(session_hash: str) -> str:
    """
    Create the necessary directory structure for a session.

    Args:
        session_hash: Hash identifying the session.

    Returns:
        Absolute path to the session's base directory.
    """
    base_dir = Path(OUTPUT_DIR).resolve() / session_hash # Use absolute path

    # Define subdirectories relative to the base directory
    subdirs = [
        "html",
        "pdf",
        "www",
        "www/assets",
        "logs",
        "mappings",
        "reports", # For snapshot reports
    ]

    try:
        # Create base directory first
        base_dir.mkdir(parents=True, exist_ok=True)

        # Create all subdirectories
        for sub in subdirs:
            (base_dir / sub).mkdir(exist_ok=True)

        logger.debug(f"Ensured output directory structure exists for session {session_hash} at {base_dir}")

        # Copy static assets (CSS, etc.) needed for viewing logs/reports in browser
        copy_assets(session_hash) # Call asset copy function

    except OSError as e:
        logger.error(f"Failed to create directory structure for session {session_hash} at {base_dir}: {e}", exc_info=True)
        raise RuntimeError(f"Could not create output directories: {e}") from e

    return str(base_dir)


def copy_assets(session_hash: str) -> None:
    """
    Copy static assets (e.g., CSS for log viewer) to the session's www directory.
    """
    try:
        # Use absolute path for session directory
        session_www_assets_dir = Path(OUTPUT_DIR).resolve() / session_hash / "www" / "assets"
        # Define template assets relative to this file's location
        template_assets_dir = Path(__file__).resolve().parent.parent / "templates" / "assets"

        if not template_assets_dir.is_dir():
            logger.warning(f"Template assets directory not found: {template_assets_dir}")
            return

        # Ensure target directory exists (should be created by create_output_dir)
        session_www_assets_dir.mkdir(exist_ok=True)

        # Copy files
        for asset_file in template_assets_dir.iterdir():
            if asset_file.is_file():
                src = asset_file
                dst = session_www_assets_dir / asset_file.name
                try:
                    # Simple binary copy
                    with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
                        fdst.write(fsrc.read())
                    logger.debug(f"Copied asset {asset_file.name} to {dst}")
                except IOError as e:
                    logger.error(f"Error copying asset {src} to {dst}: {e}")

    except Exception as e:
        # Catch any other unexpected error during asset copying
        logger.error(f"Unexpected error copying assets for session {session_hash}: {e}", exc_info=True)


def get_session_dir(session_hash: Optional[str] = None) -> str:
    """
    Get the absolute directory path for a session.

    Args:
        session_hash: Hash identifying the session, or None to use current session.

    Returns:
        Absolute path string to the session directory.

    Raises:
        ValueError: If no session hash is provided and no active session is found.
    """
    if session_hash is None:
        session_hash = get_current_session() # Reads from status.json
        if not session_hash:
            raise ValueError("No active session hash found. Cannot determine session directory.")

    # Use Path objects for reliable path joining and resolution
    session_path = Path(OUTPUT_DIR).resolve() / session_hash
    return str(session_path)


def compute_file_hash(file_path: str) -> str:
    """
    Compute SHA256 hash of file contents efficiently.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal hash string.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If there's an error reading the file.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read the file in chunks
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        hex_digest = sha256_hash.hexdigest()
        logger.debug(f"Computed SHA256 hash for {file_path}: {hex_digest[:12]}...")
        return hex_digest
    except FileNotFoundError:
        logger.error(f"File not found for hashing: {file_path}")
        raise
    except IOError as e:
        logger.error(f"IOError hashing file {file_path}: {e}")
        raise IOError(f"Could not read file for hashing: {file_path}") from e
    except Exception as e:
         logger.error(f"Unexpected error hashing file {file_path}: {e}", exc_info=True)
         raise RuntimeError(f"Hashing failed for {file_path}") from e


def generate_execution_id() -> str:
    """
    Generate a short, unique-ish execution ID based on timestamp hash.

    Returns:
        8-character hexadecimal string ID.
    """
    timestamp = str(datetime.now().timestamp()).encode()
    return hashlib.sha256(timestamp).hexdigest()[:8]

# --- Legacy sessions.json functions (Consider removing if metadata.json is sufficient) ---

def get_sessions_data() -> Dict[str, Dict[str, Any]]:
    """
    Load the sessions data from sessions.json. (Legacy)
    """
    sessions_path = Path(SESSIONS_FILE)
    if not sessions_path.exists():
        return {}
    try:
        with open(sessions_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Could not read legacy sessions file {sessions_path}: {e}. Returning empty data.")
        return {}

def save_sessions_data(sessions_data: Dict[str, Dict[str, Any]]) -> None:
    """
    Save the sessions data to sessions.json. (Legacy)
    """
    sessions_path = Path(SESSIONS_FILE)
    try:
        with open(sessions_path, 'w', encoding='utf-8') as f:
            json.dump(sessions_data, f, indent=2)
        logger.debug(f"Saved legacy sessions data to {sessions_path}")
    except (IOError, TypeError) as e:
        logger.error(f"Failed to save legacy sessions data to {sessions_path}: {e}")

def update_session_data(session_hash: str, operation: str, document_type: Optional[str] = None) -> None:
    """
    Update the legacy session data in sessions.json. (Legacy)
    """
    sessions_data = get_sessions_data()
    session_data = sessions_data.get(session_hash, {})
    now = datetime.now().isoformat()
    session_data.update({
        "last_updated": now,
        "last_operation": operation,
        "output_folder": str(Path(OUTPUT_DIR).resolve() / session_hash), # Use consistent path
    })
    if document_type:
        session_data["document_type"] = document_type
    sessions_data[session_hash] = session_data
    save_sessions_data(sessions_data)
    logger.info(f"Updated legacy session data in {SESSIONS_FILE}: hash={session_hash}, operation={operation}")

# --- End of core/session.py ---