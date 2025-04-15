#!/usr/bin/env python
"""
Simple script to create an admin user for the dashboard.
"""
import sys
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import the create_user function
try:
    from core.auth.auth_db_manager import create_user, init_auth_db
except ImportError:
    logger.error("Failed to import auth modules. Make sure you're running this from the project root directory.")
    sys.exit(1)

def main():
    """Create an admin user with the specified credentials."""
    username = "admin"
    password = "4334.4334"
    role = "admin"
    
    logger.info(f"Creating admin user '{username}'...")
    
    # Initialize the auth database if it doesn't exist
    init_auth_db()
    
    # Create the user
    success = create_user(username, password, role)
    
    if success:
        logger.info(f"Admin user '{username}' created successfully with role '{role}'")
        logger.info("You can now log in to the dashboard with these credentials.")
    else:
        logger.error(f"Failed to create user '{username}'. The username may already exist.")
        logger.info("If the user already exists, you may need to update the password using the user_password command.")

if __name__ == "__main__":
    main()
