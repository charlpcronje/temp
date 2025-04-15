#!/usr/bin/env python
"""
Activate a session by updating the status.json file with the provided session hash.
"""

import json
import sys
import os
import logging
from typing import Dict, Any, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_status() -> Dict[str, Any]:
    """
    Load the current status from status.json
    
    Returns:
        Dict containing the current status
    """
    try:
        with open("status.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        logger.warning("status.json not found, creating new status")
        return {"active_session": False}
    except json.JSONDecodeError:
        logger.warning("status.json is invalid, creating new status")
        return {"active_session": False}

def save_status(status: Dict[str, Any]) -> None:
    """
    Save the status to status.json
    
    Args:
        status: Dict containing the status to save
    """
    with open("status.json", "w") as f:
        json.dump(status, f, indent=2)

def activate_session(session_hash: str) -> None:
    """
    Activate a session by updating the status.json file
    
    Args:
        session_hash: Hash of the session to activate
    """
    # Check if the session directory exists
    session_dir = os.path.join("output", session_hash)
    if not os.path.isdir(session_dir):
        logger.error(f"Session directory not found: {session_dir}")
        print(f"Error: Session {session_hash} not found")
        return
    
    # Load current status
    status = load_status()
    
    # Get document type from session metadata if available
    document_type = None
    metadata_path = os.path.join(session_dir, "metadata.json")
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
                document_type = metadata.get("document_type")
        except Exception as e:
            logger.warning(f"Error reading metadata: {e}")
    
    # Get last operation from session metadata if available
    last_operation = None
    if os.path.exists(metadata_path):
        try:
            with open(metadata_path, "r") as f:
                metadata = json.load(f)
                last_operation = metadata.get("last_operation")
        except Exception as e:
            logger.warning(f"Error reading metadata: {e}")
    
    # Update status
    status["active_session"] = True
    status["session_hash"] = session_hash
    
    # Update document type if available
    if document_type:
        status["current_state"] = status.get("current_state", {})
        status["current_state"]["document_type"] = document_type
    
    # Update last operation if available
    if last_operation:
        status["last_operation"] = last_operation
    
    # Save updated status
    save_status(status)
    
    logger.info(f"Session {session_hash} activated")
    print(f"Session {session_hash} activated successfully")

def main():
    """
    Main function to activate a session from command line
    """
    if len(sys.argv) < 2:
        print("Usage: python activate_session.py <session_hash>")
        return
    
    session_hash = sys.argv[1]
    activate_session(session_hash)

if __name__ == "__main__":
    main()
