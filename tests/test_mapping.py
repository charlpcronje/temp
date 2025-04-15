#!/usr/bin/env python
"""
Test script for field mapping functionality
"""

import os
import json
import sys
import shutil
import logging

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.session import get_current_session, get_session_dir
from core.mapper import generate_mapping_file, load_mapping
from core.validator import validate_data

# Configure logging
logging.basicConfig(level=logging.INFO, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_mapping_flow():
    """Test the field mapping flow to ensure it respects existing mappings"""
    
    # 1. Get current session hash
    session_hash = get_current_session()
    if not session_hash:
        logger.error("No active session found")
        return False
    
    logger.info(f"Testing mapping flow for session: {session_hash}")
    
    # 2. Check for existing mapping
    session_dir = get_session_dir(session_hash)
    mapping_path = os.path.join(session_dir, "mappings", f"{session_hash}_mapping.json")
    mapping_exists = os.path.isfile(mapping_path)
    
    if mapping_exists:
        # If mapping exists, back it up
        backup_path = f"{mapping_path}.bak"
        logger.info(f"Backing up existing mapping to {backup_path}")
        shutil.copy2(mapping_path, backup_path)
        
        # Load and print current mapping
        try:
            with open(mapping_path, 'r') as f:
                existing_mapping = json.load(f)
            logger.info(f"Existing mapping has {len(existing_mapping)} entries")
            logger.info(f"Mapping entries: {json.dumps(existing_mapping, indent=2)}")
        except Exception as e:
            logger.error(f"Error reading existing mapping: {e}")
    else:
        logger.info("No existing mapping found")
    
    # 3. Generate mapping file
    try:
        logger.info("Generating mapping file...")
        mapping_info = generate_mapping_file()
        
        # Check if mapping was created or loaded
        if mapping_exists:
            logger.info("Existing mapping should have been loaded")
        else:
            logger.info("New mapping should have been created")
        
        # Print mapping information
        mapped_fields = mapping_info.get("mapped_fields", {})
        logger.info(f"Mapping contains {len(mapped_fields)} mapped fields")
        logger.info(f"Mapped fields: {json.dumps(mapped_fields, indent=2)}")
        
        # Get missing required fields
        missing_required = mapping_info.get("missing_required", [])
        if missing_required:
            logger.warning(f"Missing required fields: {', '.join(missing_required)}")
        else:
            logger.info("No missing required fields")
        
        return True
    except Exception as e:
        logger.error(f"Error in mapping process: {e}")
        return False

if __name__ == "__main__":
    logger.info("Starting mapping test")
    result = test_mapping_flow()
    logger.info(f"Test {'completed successfully' if result else 'failed'}")
