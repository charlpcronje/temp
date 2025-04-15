# API Documentation and Dashboard Requirements

## 3. Configuration Updates for Static Files and Authentication

Update the JSON configuration in `config/dev.json` and `config/prod.json` to include database settings for the dashboard:

```json
{
  "application": {
    "name": "Document Generator System",
    "version": "1.1.0",
    "author": "Your Organization",
    "description": "Generates various types of documents from Excel records"
  },
  
  /* ... existing configuration ... */
  
  "dashboard": {
    "auth": {
      "driver": "sqlite",  // Options: sqlite, mysql
      "sqlite": {
        "db_path": "dashboard.db"
      },
      "mysql": {
        "host": "localhost",
        "port": 3306,
        "database": "dashboard_db",
        "username": "dashboard_user",
        "password": "secure_password"
      },
      "session_secret": "your-secret-key-for-sessions",
      "token_expiry": 86400  // 24 hours in seconds
    },
    "logs_dir": "./public/logs",
    "upload_limits": {
      "max_file_size": 10485760,  // 10MB in bytes
      "allowed_extensions": [".csv", ".xlsx", ".xls"]
    }
  },
  
  "api": {
    "base_url": "http://localhost:8000",
    "auth_enabled": true,
    "auth_token": "dev-secret-key",
    "static_files": {
      "enabled": true,
      "public_dir": "./public",
      "logs_dir": "./public/logs"
    }
  }
}
```

## 4. API Modifications for Static File Serving

To update the API to serve files from the public directory and log files, add this to your `api.py`:

```python
from fastapi.staticfiles import StaticFiles
from pathlib import Path
import os
import shutil

# Load configuration
config = load_config()
api_config = config.get("api", {})
static_config = api_config.get("static_files", {})

# Mount static files if enabled
if static_config.get("enabled", False):
    public_dir = static_config.get("public_dir", "./public")
    logs_dir = static_config.get("logs_dir", "./public/logs")
    
    # Ensure directories exist
    os.makedirs(public_dir, exist_ok=True)
    os.makedirs(logs_dir, exist_ok=True)
    
    # Mount static files
    app.mount("/static", StaticFiles(directory=public_dir), name="static")
    
    # Mount logs directory separately to ensure it's accessible
    app.mount("/logs", StaticFiles(directory=logs_dir), name="logs")

# Add endpoint to copy session directory to logs
@app.post("/session/{session_hash}/copy-to-logs")
async def copy_session_to_logs(session_hash: str, api_key: str = Header(None, alias="X-API-Key")):
    """
    Copy a session directory to the logs directory for dashboard access.
    """
    # Check API key
    if _check_api_auth(api_key) is False:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")
    
    # Get session directory
    session_dir = get_session_dir(session_hash)
    if not os.path.exists(session_dir):
        raise HTTPException(status_code=404, detail=f"Session directory not found: {session_hash}")
    
    # Get logs directory from config
    logs_dir = static_config.get("logs_dir", "./public/logs")
    os.makedirs(logs_dir, exist_ok=True)
    
    # Target directory
    target_dir = os.path.join(logs_dir, session_hash)
    
    # Check if target already exists
    if os.path.exists(target_dir):
        raise HTTPException(status_code=400, detail=f"Session already exists in logs: {session_hash}")
    
    try:
        # Copy directory
        shutil.copytree(session_dir, target_dir)
        return {"success": True, "message": f"Session {session_hash} copied to logs"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to copy session: {str(e)}")
```

## 5. React Dashboard Prompt

Use the following prompt for a new context window to create the React dashboard:

```
I need a React dashboard for a document processing system using ShadCN UI components. Here are the specific requirements:

1. Authentication
   - Login screen with username/password authentication
   - Store authentication token in localStorage
   - Protected routes for authenticated users only
   - Support for different user roles (admin, user)

2. Dashboard Layout
   - Sidebar navigation with responsive design
   - Header with user info and logout button
   - Dark/light mode toggle
   - Main content area for different views

3. Session Management
   - Display list of processing sessions (identified by hash)
   - Allow renaming sessions with custom names
   - Display session details (date, file count, status)
   - Filter and sort sessions

4. File Upload
   - Drag and drop area for CSV/Excel files
   - Progress indicator for upload
   - Validation for file types and size

5. Processing Workflow
   - Step-by-step interface matching CLI endpoints:
     a. Import: Upload or select file
     b. Validate: Show validation results and detected document type
     c. Map: Display and edit field mappings
     d. HTML: Generate and preview HTML files
     e. PDF: Generate and preview PDF files
   - Progress tracking for each step
   - Error handling and display

6. Log Viewer
   - Browse logs for each session
   - Display HTML reports and forms
   - PDF viewer integration
   - Download options for generated files

7. User Management (Admin only)
   - Create, edit, delete users
   - Assign roles
   - Reset passwords

8. Technical Requirements
   - React with TypeScript
   - ShadCN UI components
   - React Router for navigation
   - React Query for API calls
   - Responsive design for mobile and desktop
   - Client-side validation
   - Error boundary handling

9. API Integration
   - The API serves files from ./public
   - Logs are stored in ./public/logs
   - Authentication against SQLite/MySQL (configurable)
   - All CLI commands available via API

Please provide a comprehensive implementation with proper code organization, state management, and responsive design. Include clear documentation for how to use and extend the dashboard.
```

This prompt provides all the necessary details for someone to build the React dashboard with ShadCN components, integrating with the API you've developed.

## 6. Additional Steps

After implementing these changes, you'll need to:

1. Create database schema for user authentication:

```sql
-- SQLite schema
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE TABLE sessions (
    hash TEXT PRIMARY KEY,
    name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    source_file TEXT,
    document_type TEXT,
    status TEXT
);
```

2. Add initial user:

```sql
-- Default admin user with password 'admin123'
INSERT INTO users (username, password_hash, role) 
VALUES ('admin', 'pbkdf2:sha256:150000$HASH_VALUE', 'admin');
```

3. Set up startup script that creates the default folders:

```bash
#!/bin/bash
mkdir -p ./public/logs
chmod -R 755 ./public
```

With these components, you'll have a comprehensive document processing system with:
- Well-documented API (OpenAPI + Postman)
- Static file serving capabilities
- User authentication and authorization
- Database support for both SQLite and MySQL
- All the necessary configuration for the React dashboard

Would you like me to elaborate on any specific part of this implementation?