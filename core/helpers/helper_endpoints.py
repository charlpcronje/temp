"""
Helper endpoints for providing troubleshooting guidance to users.
"""

import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

# Create router
helper_router = APIRouter(prefix="/helper", tags=["helpers"])

# Pydantic models
class HelperResponse(BaseModel):
    issue: str
    title: str
    description: str
    solution: str
    command: Optional[str] = None
    command_location: Optional[str] = None
    documentation_link: Optional[str] = None


# Define common issues and their solutions
HELPER_ISSUES = {
    "failedDashboardData": {
        "title": "Failed to Load Dashboard Data",
        "description": "The dashboard cannot access the logs directory. This typically happens when the logs directory is not properly configured or created.",
        "solution": "Create a symbolic link from 'public/logs' to the 'output' directory where logs are generated.",
        "command": "mklink /D public\\logs output",
        "command_location": "c:\\xampp\\htdocs\\DocTypeGen"
    },
    "authenticationFailed": {
        "title": "Authentication Failed",
        "description": "Failed to authenticate user. This may be due to incorrect credentials or issues with the authentication system.",
        "solution": "Ensure the authentication server is running and your credentials are correct. You can also try restarting the API server.",
        "command": "python api.py",
        "command_location": "c:\\xampp\\htdocs\\DocTypeGen"
    },
    "sessionNotFound": {
        "title": "Session Not Found",
        "description": "The requested session could not be found. This may be because the session has expired or was deleted.",
        "solution": "Start a new processing session by clicking the 'New Session' button in the dashboard.",
    },
    "missingLogs": {
        "title": "Missing Logs",
        "description": "The system cannot find log files for the current session.",
        "solution": "Ensure the logs directory is properly configured and the session has generated logs. You may need to run a command that generates logs first.",
    }
}


@helper_router.get("/{issue_id}", response_model=HelperResponse)
async def get_helper(issue_id: str):
    """
    Get help for a specific issue.
    
    Args:
        issue_id: The ID of the issue to get help for
        
    Returns:
        HelperResponse object with guidance
    """
    if issue_id not in HELPER_ISSUES:
        raise HTTPException(status_code=404, detail=f"Helper for issue '{issue_id}' not found")
    
    issue_info = HELPER_ISSUES[issue_id]
    
    return {
        "issue": issue_id,
        **issue_info
    }


@helper_router.get("/", response_model=Dict[str, HelperResponse])
async def list_helpers():
    """
    List all available helpers.
    
    Returns:
        Dictionary of issue IDs to helper information
    """
    return {
        issue_id: {
            "issue": issue_id,
            **issue_info
        }
        for issue_id, issue_info in HELPER_ISSUES.items()
    }
