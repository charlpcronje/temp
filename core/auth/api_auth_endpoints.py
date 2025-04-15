#!/usr/bin/env python
"""
API Authentication Endpoints - Adding authentication functionality to the API.
This module will be imported in api.py.
"""

import logging
from typing import Dict, Any, Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Header, Security
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel

# Import our auth modules
from core.auth import jwt_auth
from core.auth.auth_db_manager import list_users, change_user_role, change_user_password, update_user_status

# Configure logging
logger = logging.getLogger(__name__)

# Create a router for auth endpoints
auth_router = APIRouter(prefix="/auth", tags=["authentication"])

# OAuth2 password flow (used for Swagger UI authentication)
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

# --- Pydantic Models for request/response validation ---

class LoginRequest(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    token: str
    user: Dict[str, Any]

class UserResponse(BaseModel):
    id: int
    username: str
    role: str
    
class UserListResponse(BaseModel):
    users: List[Dict[str, Any]]

class UserUpdateRequest(BaseModel):
    username: str
    role: Optional[str] = None
    is_active: Optional[bool] = None
    password: Optional[str] = None

class UserUpdateResponse(BaseModel):
    success: bool
    username: str
    message: str

# --- Authentication Dependency ---

def get_current_user(authorization: Optional[str] = Header(None)) -> Dict[str, Any]:
    """
    Dependency to get the current authenticated user from the Authorization header.
    
    Args:
        authorization: Authorization header value (Bearer token)
        
    Returns:
        User information dictionary if authenticated
        
    Raises:
        HTTPException: If authentication fails
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Split "Bearer <token>"
    try:
        scheme, token = authorization.split()
        if scheme.lower() != "bearer":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication scheme. Use Bearer token",
                headers={"WWW-Authenticate": "Bearer"}
            )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Use 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    # Validate token
    is_valid, user_info = jwt_auth.validate_jwt_token(token)
    
    if not is_valid or not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user_info

def get_admin_user(user: Dict[str, Any] = Depends(get_current_user)) -> Dict[str, Any]:
    """
    Dependency to get the current authenticated admin user.
    
    Args:
        user: Current authenticated user (from get_current_user)
        
    Returns:
        User information if the user is an admin
        
    Raises:
        HTTPException: If the user is not an admin
    """
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    return user

# --- Endpoints ---

@auth_router.post("/login", response_model=TokenResponse)
async def login(login_data: LoginRequest):
    """
    Authenticate a user and provide a JWT token.
    """
    logger.info(f"Login attempt for user: {login_data.username}")
    
    success, token, user_info = jwt_auth.login_user(
        login_data.username, 
        login_data.password
    )
    
    if not success or not token or not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )
    
    return {
        "token": token,
        "user": user_info
    }

@auth_router.post("/token", response_model=TokenResponse)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, get an access token for future requests.
    Used primarily for Swagger UI authentication.
    """
    success, token, user_info = jwt_auth.login_user(
        form_data.username, 
        form_data.password
    )
    
    if not success or not token or not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return {
        "token": token,
        "user": user_info
    }

@auth_router.get("/me", response_model=UserResponse)
async def get_user_info(user: Dict[str, Any] = Depends(get_current_user)):
    """
    Get information about the currently authenticated user.
    """
    return {
        "id": user["id"],
        "username": user["username"],
        "role": user["role"]
    }

@auth_router.get("/verify")
async def verify_token(api_key: str = Header(None, alias="X-API-Key")):
    """
    Verify that a token is valid without requiring full authentication.
    
    Returns:
        JSON object with token validity status and basic user info if valid
    """
    if not api_key:
        return {"valid": False, "message": "No token provided"}
    
    token = api_key  # The token is sent directly in the X-API-Key header
    
    try:
        # Verify the token
        is_valid, payload = jwt_auth.validate_jwt_token(token)
        
        if is_valid and payload:
            return {
                "valid": True,
                "user": {
                    "id": payload["id"],
                    "username": payload["username"],
                    "role": payload["role"]
                }
            }
        
    except Exception as e:
        logger.warning(f"Token verification failed: {e}")
    
    return {"valid": False, "message": "Invalid token"}

@auth_router.get("/users", response_model=UserListResponse)
async def get_users(_: Dict[str, Any] = Depends(get_admin_user)):
    """
    List all users in the system. Requires admin privileges.
    """
    users = list_users()
    return {"users": users}

@auth_router.put("/users", response_model=UserUpdateResponse)
async def update_user(
    update_data: UserUpdateRequest,
    _: Dict[str, Any] = Depends(get_admin_user)
):
    """
    Update a user's role, status, or password. Requires admin privileges.
    """
    username = update_data.username
    success = True
    message = "User updated successfully"
    
    # Update role if provided
    if update_data.role is not None:
        role_success = change_user_role(username, update_data.role)
        if not role_success:
            success = False
            message = f"Failed to update role for user '{username}'"
    
    # Update active status if provided
    if update_data.is_active is not None and success:
        status_success = update_user_status(username, update_data.is_active)
        if not status_success:
            success = False
            message = f"Failed to update status for user '{username}'"
    
    # Update password if provided
    if update_data.password is not None and success:
        password_success = change_user_password(username, update_data.password)
        if not password_success:
            success = False
            message = f"Failed to update password for user '{username}'"
    
    return {
        "success": success,
        "username": username,
        "message": message
    }

def setup_auth_router(app, jwt_secret: str = None, jwt_expiration_hours: int = 24):
    """
    Configure the JWT authentication system and attach the auth router to the FastAPI app.
    
    Args:
        app: FastAPI app instance
        jwt_secret: Secret key for JWT signing (will use default if None)
        jwt_expiration_hours: Token expiration time in hours
    """
    # Configure JWT settings if provided
    if jwt_secret:
        jwt_auth.configure_jwt(
            secret_key=jwt_secret,
            expiration_hours=jwt_expiration_hours
        )
    
    # Include the auth router in the app
    app.include_router(auth_router)
    
    logger.info("Authentication router configured and attached to API")