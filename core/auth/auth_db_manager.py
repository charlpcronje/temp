#!/usr/bin/env python
"""
Authentication Database Manager - Handle user authentication database operations.
File path: core/auth/auth_db_manager.py
"""

import os
import sqlite3
import hashlib
import logging
import secrets
from typing import Dict, Optional, List, Any, Tuple

# Configure logging
logger = logging.getLogger(__name__)

# Constants
AUTH_DB_PATH = "auth.db"

def init_auth_db() -> None:
    """
    Initialize the authentication database if it doesn't exist.
    Creates the database file and required tables.
    """
    if not os.path.exists(AUTH_DB_PATH):
        logger.info(f"Creating new authentication database at {AUTH_DB_PATH}")
    
    conn = sqlite3.connect(AUTH_DB_PATH)
    cursor = conn.cursor()
    
    # Create users table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        salt TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'user',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        last_login TIMESTAMP,
        is_active INTEGER DEFAULT 1
    )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Authentication database initialized successfully")

def hash_password(password: str, salt: Optional[str] = None) -> Tuple[str, str]:
    """
    Hash a password with a salt using PBKDF2 with SHA-256.
    
    Args:
        password: The plaintext password to hash
        salt: Optional salt to use (generates a new one if not provided)
        
    Returns:
        Tuple of (password_hash, salt)
    """
    if salt is None:
        salt = secrets.token_hex(16)  # 16 bytes = 32 hex chars
    
    # Use the hashlib pbkdf2_hmac function for better security
    key = hashlib.pbkdf2_hmac(
        'sha256',  # The hash algorithm
        password.encode('utf-8'),  # Convert the password to bytes
        salt.encode('utf-8'),  # Convert the salt to bytes
        100000,  # 100,000 iterations (recommended minimum)
        dklen=64  # Get a 64-byte key
    )
    
    # Convert the key to a hex string
    password_hash = key.hex()
    
    return password_hash, salt

def verify_password(password: str, password_hash: str, salt: str) -> bool:
    """
    Verify a password against a hash and salt.
    
    Args:
        password: The plaintext password to check
        password_hash: The stored password hash
        salt: The stored salt
        
    Returns:
        True if the password matches, False otherwise
    """
    calculated_hash, _ = hash_password(password, salt)
    return calculated_hash == password_hash

def create_user(username: str, password: str, role: str = 'user') -> bool:
    """
    Create a new user in the authentication database.
    
    Args:
        username: The username for the new user
        password: The password for the new user
        role: The role to assign to the user (default: 'user')
        
    Returns:
        True if user was created successfully, False otherwise
    """
    # Ensure the auth database exists
    init_auth_db()
    
    # Hash the password
    password_hash, salt = hash_password(password)
    
    try:
        conn = sqlite3.connect(AUTH_DB_PATH)
        cursor = conn.cursor()
        
        # Check if username already exists
        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        if cursor.fetchone():
            logger.warning(f"User '{username}' already exists")
            conn.close()
            return False
        
        # Insert new user
        cursor.execute(
            "INSERT INTO users (username, password_hash, salt, role) VALUES (?, ?, ?, ?)",
            (username, password_hash, salt, role)
        )
        
        conn.commit()
        logger.info(f"User '{username}' created successfully with role '{role}'")
        conn.close()
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Database error creating user: {e}")
        return False

def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Authenticate a user with username and password.
    
    Args:
        username: The username to authenticate
        password: The password to check
        
    Returns:
        Dict with user information if authenticated, None otherwise
    """
    try:
        conn = sqlite3.connect(AUTH_DB_PATH)
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
        cursor = conn.cursor()
        
        # Get the user record
        cursor.execute(
            "SELECT id, username, password_hash, salt, role, is_active FROM users WHERE username = ?",
            (username,)
        )
        user = cursor.fetchone()
        
        if not user:
            logger.warning(f"Authentication failed: User '{username}' not found")
            conn.close()
            return None
        
        # Convert to dict for easier handling
        user_dict = dict(user)
        
        # Check if user is active
        if not user_dict['is_active']:
            logger.warning(f"Authentication failed: User '{username}' is inactive")
            conn.close()
            return None
        
        # Verify the password
        if not verify_password(password, user_dict['password_hash'], user_dict['salt']):
            logger.warning(f"Authentication failed: Invalid password for user '{username}'")
            conn.close()
            return None
        
        # Update last login time
        cursor.execute(
            "UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?",
            (user_dict['id'],)
        )
        conn.commit()
        
        # Return user info without the password hash and salt
        user_info = {
            'id': user_dict['id'],
            'username': user_dict['username'],
            'role': user_dict['role']
        }
        
        conn.close()
        return user_info
        
    except sqlite3.Error as e:
        logger.error(f"Database error during authentication: {e}")
        return None

def list_users() -> List[Dict[str, Any]]:
    """
    List all users in the database.
    
    Returns:
        List of user dictionaries (excluding password and salt)
    """
    try:
        # Ensure the auth database exists
        init_auth_db()
        
        conn = sqlite3.connect(AUTH_DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT id, username, role, created_at, last_login, is_active FROM users"
        )
        
        users = [dict(row) for row in cursor.fetchall()]
        conn.close()
        
        return users
        
    except sqlite3.Error as e:
        logger.error(f"Database error listing users: {e}")
        return []

def update_user_status(username: str, is_active: bool) -> bool:
    """
    Activate or deactivate a user.
    
    Args:
        username: The username to update
        is_active: True to activate, False to deactivate
        
    Returns:
        True if updated successfully, False otherwise
    """
    try:
        conn = sqlite3.connect(AUTH_DB_PATH)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        if not cursor.fetchone():
            logger.warning(f"User '{username}' not found")
            conn.close()
            return False
        
        # Update user status
        cursor.execute(
            "UPDATE users SET is_active = ? WHERE username = ?",
            (1 if is_active else 0, username)
        )
        
        conn.commit()
        status = "activated" if is_active else "deactivated"
        logger.info(f"User '{username}' {status} successfully")
        conn.close()
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Database error updating user status: {e}")
        return False

def change_user_password(username: str, new_password: str) -> bool:
    """
    Change a user's password.
    
    Args:
        username: The username whose password to change
        new_password: The new password
        
    Returns:
        True if changed successfully, False otherwise
    """
    try:
        conn = sqlite3.connect(AUTH_DB_PATH)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        if not cursor.fetchone():
            logger.warning(f"User '{username}' not found")
            conn.close()
            return False
        
        # Hash the new password
        password_hash, salt = hash_password(new_password)
        
        # Update the password
        cursor.execute(
            "UPDATE users SET password_hash = ?, salt = ? WHERE username = ?",
            (password_hash, salt, username)
        )
        
        conn.commit()
        logger.info(f"Password changed successfully for user '{username}'")
        conn.close()
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Database error changing password: {e}")
        return False

def change_user_role(username: str, new_role: str) -> bool:
    """
    Change a user's role.
    
    Args:
        username: The username whose role to change
        new_role: The new role (e.g., 'user', 'admin')
        
    Returns:
        True if changed successfully, False otherwise
    """
    try:
        conn = sqlite3.connect(AUTH_DB_PATH)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        if not cursor.fetchone():
            logger.warning(f"User '{username}' not found")
            conn.close()
            return False
        
        # Update the role
        cursor.execute(
            "UPDATE users SET role = ? WHERE username = ?",
            (new_role, username)
        )
        
        conn.commit()
        logger.info(f"Role changed to '{new_role}' for user '{username}'")
        conn.close()
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Database error changing role: {e}")
        return False

def delete_user(username: str) -> bool:
    """
    Delete a user from the database.
    
    Args:
        username: The username to delete
        
    Returns:
        True if deleted successfully, False otherwise
    """
    try:
        conn = sqlite3.connect(AUTH_DB_PATH)
        cursor = conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT username FROM users WHERE username = ?", (username,))
        if not cursor.fetchone():
            logger.warning(f"User '{username}' not found")
            conn.close()
            return False
        
        # Delete the user
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        
        conn.commit()
        logger.info(f"User '{username}' deleted successfully")
        conn.close()
        return True
        
    except sqlite3.Error as e:
        logger.error(f"Database error deleting user: {e}")
        return False

# Initialize database when this module is imported
init_auth_db()