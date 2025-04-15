#!/usr/bin/env python
"""
Symbols - Platform-appropriate symbols for CLI output
"""

import os
import dotenv

# Load environment variables
dotenv.load_dotenv()

# Get the OS setting (lowercase for consistent matching)
SYSTEM_OS = os.getenv("SYSTEM_OS", "windows").lower()

# Define symbols for different platforms
if SYSTEM_OS == "windows":
    # Use ASCII compatible symbols for Windows command prompt
    CHECK_MARK = "+"  # Simple plus sign instead of Unicode checkmark
    CROSS_MARK = "x"  # Simple x instead of Unicode cross
    BULLET = "*"      # Simple asterisk instead of Unicode bullet
    ARROW = "->"      # Simple arrow instead of Unicode arrow
else:
    # Use Unicode symbols for Linux/Mac terminals which support UTF-8
    CHECK_MARK = "✓"  # Unicode checkmark
    CROSS_MARK = "✗"  # Unicode cross
    BULLET = "•"      # Unicode bullet
    ARROW = "→"       # Unicode arrow

# Function to get symbols dynamically
def get_symbol(name):
    """
    Get a symbol by name, adjusting for the current platform.
    
    Args:
        name: Symbol name (CHECK_MARK, CROSS_MARK, BULLET, ARROW)
        
    Returns:
        String with appropriate symbol for platform
    """
    symbols = {
        "CHECK_MARK": CHECK_MARK,
        "CROSS_MARK": CROSS_MARK,
        "BULLET": BULLET,
        "ARROW": ARROW
    }
    return symbols.get(name, "")
