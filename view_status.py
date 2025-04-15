#!/usr/bin/env python
"""
View the contents of the status.json file.
"""

import json
import sys
import os
from typing import Dict, Any

def view_status():
    """
    View the contents of the status.json file.
    """
    if not os.path.exists("status.json"):
        print("status.json file not found.")
        return
    
    try:
        with open("status.json", "r") as f:
            status_data = json.load(f)
        
        print("Status.json contents:")
        print("-" * 80)
        
        print(f"Last Updated: {status_data.get('last_updated', 'N/A')}")
        
        current_state = status_data.get("current_state", {})
        if current_state:
            print("\nCurrent State:")
            print(f"  Session Hash: {current_state.get('hash', 'N/A')}")
            print(f"  Last Operation: {current_state.get('last_operation', 'N/A')}")
            print(f"  Document Type: {current_state.get('document_type', 'N/A')}")
            print(f"  Imported File: {current_state.get('imported_file', 'N/A')}")
            print(f"  Output Folder: {current_state.get('output_folder', 'N/A')}")
            print(f"  SQLite DB File: {current_state.get('sqlite_db_file', 'N/A')}")
        else:
            print("\nNo current state found.")
        
    except Exception as e:
        print(f"Error reading status.json: {e}")

if __name__ == "__main__":
    view_status()
