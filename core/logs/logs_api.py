"""
Logs API - Endpoints for retrieving log data from the output directory
"""

import os
import json
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime

# Import core modules
from core.session import get_current_session, get_session_dir

# Configure logging
logger = logging.getLogger(__name__)

# Create router
logs_router = APIRouter(tags=["logs"])

# Pydantic models for logs API
class LogDirectoryModel(BaseModel):
    hash: str
    name: Optional[str] = None
    timestamp: datetime
    file_count: int
    processed_files: int = 0
    validation_errors: int = 0
    status: str = "completed"

class LogInfoModel(BaseModel):
    hash: str
    name: Optional[str] = None
    timestamp: datetime
    files: List[Dict[str, Any]]
    validation_results: Optional[Dict[str, Any]] = None
    mapping: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

def scan_output_directory() -> List[LogDirectoryModel]:
    """
    Scan the output directory for session directories and collect metadata
    
    Returns:
        List of LogDirectory objects
    """
    output_dir = os.path.abspath("output")
    logger.info(f"Scanning output directory: {output_dir}")
    
    if not os.path.exists(output_dir):
        logger.warning(f"Output directory not found: {output_dir}")
        return []
        
    log_dirs = []
    
    try:
        # List all session directories
        for entry in os.listdir(output_dir):
            dir_path = os.path.join(output_dir, entry)
            
            # Skip non-directories and hidden directories
            if not os.path.isdir(dir_path) or entry.startswith('.'):
                continue
                
            # Try to get session info
            try:
                # Check for metadata file
                metadata_path = os.path.join(dir_path, "metadata.json")
                name = None
                timestamp = datetime.fromtimestamp(os.path.getctime(dir_path))
                
                if os.path.exists(metadata_path):
                    try:
                        with open(metadata_path, 'r') as f:
                            metadata = json.load(f)
                            name = metadata.get("name")
                            if "timestamp" in metadata:
                                # Try to parse timestamp from metadata
                                try:
                                    timestamp = datetime.fromisoformat(metadata["timestamp"])
                                except (ValueError, TypeError):
                                    pass
                    except Exception as e:
                        logger.warning(f"Error reading metadata file for {entry}: {e}")
                
                # Count files
                file_count = 0
                for root, _, files in os.walk(dir_path):
                    file_count += len(files)
                
                # Check for validation errors
                validation_errors = 0
                validation_path = os.path.join(dir_path, "validation.json")
                if os.path.exists(validation_path):
                    try:
                        with open(validation_path, 'r') as f:
                            validation = json.load(f)
                            validation_errors = len(validation.get("errors", []))
                    except Exception as e:
                        logger.warning(f"Error reading validation file for {entry}: {e}")
                
                # Determine status
                status = "completed"
                if entry == get_current_session():
                    status = "active"
                
                log_dirs.append(LogDirectoryModel(
                    hash=entry,
                    name=name,
                    timestamp=timestamp,
                    file_count=file_count,
                    processed_files=file_count - 1 if file_count > 0 else 0,  # Exclude metadata file
                    validation_errors=validation_errors,
                    status=status
                ))
                
            except Exception as e:
                logger.error(f"Error processing directory {entry}: {e}")
        
        # Sort by timestamp (newest first)
        log_dirs.sort(key=lambda x: x.timestamp, reverse=True)
        
    except Exception as e:
        logger.error(f"Error scanning output directory: {e}")
    
    return log_dirs

def get_session_log_info(session_hash: str) -> LogInfoModel:
    """
    Get detailed log information for a specific session
    
    Args:
        session_hash: Session hash to get info for
        
    Returns:
        LogInfo object with detailed session information
        
    Raises:
        HTTPException: If session not found
    """
    session_dir = get_session_dir(session_hash)
    
    if not os.path.exists(session_dir):
        raise HTTPException(status_code=404, detail=f"Session {session_hash} not found")
    
    # Basic session info
    name = None
    timestamp = datetime.fromtimestamp(os.path.getctime(session_dir))
    metadata = {}
    
    # Try to get metadata
    metadata_path = os.path.join(session_dir, "metadata.json")
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
                name = metadata.get("name")
                if "timestamp" in metadata:
                    try:
                        timestamp = datetime.fromisoformat(metadata["timestamp"])
                    except (ValueError, TypeError):
                        pass
        except Exception as e:
            logger.warning(f"Error reading metadata for {session_hash}: {e}")
    
    # Get file list
    files = []
    for root, _, file_list in os.walk(session_dir):
        for file in file_list:
            file_path = os.path.join(root, file)
            rel_path = os.path.relpath(file_path, session_dir)
            
            files.append({
                "name": file,
                "path": rel_path,
                "size": os.path.getsize(file_path),
                "modified": datetime.fromtimestamp(os.path.getmtime(file_path)).isoformat()
            })
    
    # Get validation results if available
    validation_results = None
    validation_path = os.path.join(session_dir, "validation.json")
    if os.path.exists(validation_path):
        try:
            with open(validation_path, 'r') as f:
                validation_results = json.load(f)
        except Exception as e:
            logger.warning(f"Error reading validation for {session_hash}: {e}")
    
    # Get mapping if available
    mapping = None
    mapping_path = os.path.join(session_dir, "mapping.json")
    if os.path.exists(mapping_path):
        try:
            with open(mapping_path, 'r') as f:
                mapping = json.load(f)
        except Exception as e:
            logger.warning(f"Error reading mapping for {session_hash}: {e}")
    
    return LogInfoModel(
        hash=session_hash,
        name=name,
        timestamp=timestamp,
        files=files,
        validation_results=validation_results,
        mapping=mapping,
        metadata=metadata
    )

@logs_router.get("/logs", response_model=List[LogDirectoryModel])
async def list_logs():
    """
    List all session logs from the output directory
    
    Returns:
        List of session log directories
    """
    logger.info("Listing all logs")
    return scan_output_directory()

@logs_router.get("/logs/{session_hash}", response_model=LogInfoModel)
async def get_log_info(session_hash: str):
    """
    Get detailed information about a specific session log
    
    Args:
        session_hash: Hash of the session to get info for
        
    Returns:
        Detailed session log information
    """
    logger.info(f"Getting log info for session: {session_hash}")
    return get_session_log_info(session_hash)

@logs_router.post("/logs/{session_hash}/rename")
async def rename_log(session_hash: str, name: str = Query(..., description="New name for the session")):
    """
    Rename a session log
    
    Args:
        session_hash: Hash of the session to rename
        name: New name for the session
        
    Returns:
        Success status
    """
    logger.info(f"Renaming session {session_hash} to {name}")
    
    session_dir = get_session_dir(session_hash)
    if not os.path.exists(session_dir):
        raise HTTPException(status_code=404, detail=f"Session {session_hash} not found")
    
    # Update metadata
    metadata_path = os.path.join(session_dir, "metadata.json")
    metadata = {}
    
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, 'r') as f:
                metadata = json.load(f)
        except Exception as e:
            logger.warning(f"Error reading metadata for {session_hash}: {e}")
    
    # Update name
    metadata["name"] = name
    
    # Write updated metadata
    try:
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    except Exception as e:
        logger.error(f"Error updating metadata for {session_hash}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to rename session: {e}")
    
    return {"success": True}
