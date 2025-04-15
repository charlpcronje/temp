#!/usr/bin/env python
"""
JWT Authentication Module - Handle JWT token generation and validation for API authentication.
File path: core/auth/jwt_auth.py
"""

import jwt
import logging
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

# Import our auth module
from core.auth.auth_db_manager import authenticate_user, init_auth_db

# Configure logging
logger = logging.getLogger(__name__)

# Default JWT settings - should be overridden from config in practice
JWT_SECRET_KEY = "your-secret-key-change-this-in-production"  # Will be overridden from config
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24  # Token validity

def configure_jwt(secret_key: str, algorithm: str = "HS256", expiration_hours: int = 24) -> None:
    """
    Configure JWT settings.
    
    Args:
        secret_key: Secret key for JWT signing
        algorithm: JWT algorithm to use
        expiration_hours: Token expiration time in hours
    """
    global JWT_SECRET_KEY, JWT_ALGORITHM, JWT_EXPIRATION_HOURS
    
    JWT_SECRET_KEY = secret_key
    JWT_ALGORITHM = algorithm
    JWT_EXPIRATION_HOURS = expiration_hours
    
    logger.info(f"JWT configuration updated. Algorithm: {algorithm}, Expiration: {expiration_hours} hours")

def generate_jwt_token(user: Dict[str, Any]) -> str:
    """
    Generate a JWT token for a user.
    
    Args:
        user: User information dictionary (id, username, role)
        
    Returns:
        JWT token string
    """
    # Set token expiration
    exp_time = datetime.now() + timedelta(hours=JWT_EXPIRATION_HOURS)
    
    # Create payload
    payload = {
        "sub": str(user["id"]),  # Subject (user ID)
        "username": user["username"],
        "role": user["role"],
        "exp": int(time.mktime(exp_time.timetuple())),  # Expiration timestamp
        "iat": int(time.time())  # Issued at timestamp
    }
    
    # Generate token
    token = jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)
    
    return token

def validate_jwt_token(token: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Validate a JWT token and return the payload if valid.
    
    Args:
        token: JWT token to validate
        
    Returns:
        Tuple of (is_valid, payload_or_none)
    """
    try:
        # Decode and verify the token
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        
        # Extract user info from payload
        user_info = {
            "id": int(payload["sub"]),
            "username": payload["username"],
            "role": payload["role"]
        }
        
        return True, user_info
        
    except jwt.ExpiredSignatureError:
        logger.warning("Authentication failed: Token has expired")
        return False, None
        
    except jwt.InvalidTokenError:
        logger.warning("Authentication failed: Invalid token")
        return False, None
        
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        return False, None

def login_user(username: str, password: str) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
    """
    Authenticate a user and generate a JWT token if successful.
    
    Args:
        username: Username to authenticate
        password: Password to verify
        
    Returns:
        Tuple of (success, token_or_none, user_info_or_none)
    """
    # Ensure the auth database is initialized
    init_auth_db()
    
    # Authenticate the user
    user_info = authenticate_user(username, password)
    
    if not user_info:
        return False, None, None
    
    # Generate a token
    token = generate_jwt_token(user_info)
    
    return True, token, user_info