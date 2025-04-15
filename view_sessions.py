#!/usr/bin/env python
"""
View the contents of the sessions.json file.
"""

import json
import sys
import os
from typing import Dict, Any

def view_sessions():
    """
    View the contents of the sessions.json file.
    """
    if not os.path.exists("sessions.json"):
        print("sessions.json file not found.")
        return
    
    try:
        with open("sessions.json", "r") as f:
            sessions_data = json.load(f)
        
        if not sessions_data:
            print("No sessions found in sessions.json.")
            return
        
        print(f"Found {len(sessions_data)} sessions:")
        print("-" * 80)
        
        for session_hash, session_data in sessions_data.items():
            print(f"Session: {session_hash}")
            print(f"  Last Operation: {session_data.get('last_operation', 'N/A')}")
            print(f"  Last Updated: {session_data.get('last_updated', 'N/A')}")
            print(f"  Document Type: {session_data.get('document_type', 'N/A')}")
            print(f"  Output Folder: {session_data.get('output_folder', 'N/A')}")
            print("-" * 80)
        
    except Exception as e:
        print(f"Error reading sessions.json: {e}")

if __name__ == "__main__":
    view_sessions()
