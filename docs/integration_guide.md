# Integration and Usage Guide

This guide explains how to integrate the React dashboard with your DocTypeGen backend and how to use the API authentication options.

## Integration Steps

1. **Add Backend API Enhancements**
   - Add the API user management and static file routes to your `api.py` file
   - Install additional required dependencies: `pip install passlib pyjwt bcrypt`

2. **Setup Dashboard Directory**
   - Create a `dashboard` directory in your project root
   - Run the build script to initialize and build the dashboard:
   ```bash
   # Make the script executable
   chmod +x build-dashboard.sh
   # Run the script
   ./build-dashboard.sh
   ```

3. **Configure Authentication**
   - Choose between JWT and API key authentication
   - Update the backend configuration in `config/dev.json`
   - Set appropriate environment variables for the dashboard

## Authentication Options

### JWT Authentication (Recommended)

JWT authentication provides user-specific permissions and better security. It's recommended for most deployments.

**Backend Configuration:**
```json
{
  "api": {
    "auth_enabled": true,
    "auth_token": null
  }
}
```

**Dashboard Configuration:**
```
VITE_USE_JWT_AUTH=true
```

With this setup:
- Users log in with username/password
- Backend validates credentials and issues a JWT token
- Dashboard stores token in localStorage and includes it in the `X-API-Key` header
- Protected routes check JWT token validity and user role

### API Key Authentication (Simple)

API key authentication is simpler but doesn't provide user-specific permissions.

**Backend Configuration:**
```json
{
  "api": {
    "auth_enabled": true,
    "auth_token": "your-secret-api-key"
  }
}
```

**Dashboard Configuration:**
```
VITE_USE_JWT_AUTH=false
VITE_API_KEY=your-secret-api-key
```

With this setup:
- The dashboard includes the API key in the `X-API-Key` header for all requests
- Backend validates the API key against the configured value
- No user-specific permissions (all users have the same access)

## API Service for Static Files

The updated API now serves several types of files:

1. **Dashboard static files**
   - Files from `dashboard/dist` for the React app
   - Served from the root path (e.g., `/index.html`, `/assets/main.js`)

2. **Session output files**
   - HTML files: `/static/{session_hash}/html/{filename}`
   - PDF files: `/static/{session_hash}/pdf/{filename}`
   - Log files: `/static/{session_hash}/www/{filename}`

3. **SPA routing support**
   - Any path not matching an API endpoint will serve `index.html`
   - Allows client-side routing to work properly

## User Management

The API now includes user management endpoints:

- `POST /auth/login` - Authenticate user and get JWT token
- `GET /auth/verify` - Verify JWT token validity
- `GET /users` - List all users (admin only)
- `POST /users` - Create a new user (admin only)
- `PUT /users/{user_id}` - Update a user (admin only)
- `DELETE /users/{user_id}` - Delete a user (admin only)

A default admin user (username: `admin`, password: `admin`) is created on first run.

## Session Management

New API endpoints for session management:

- `GET /logs` - Get list of all sessions with metadata
- `GET /logs/{hash}` - Get detailed information about a specific session
- `POST /logs/{hash}/rename` - Rename a session

## Directory Structure after Integration

```
/
├── api.py                # FastAPI backend with user management
├── cli.py                # Command-line interface
├── commands.py           # Command registry
├── config/               # Configuration files
├── core/                 # Core business logic
├── dashboard/            # React dashboard
│   ├── dist/             # Built dashboard files
│   ├── node_modules/     # Node dependencies
│   ├── public/           # Static assets
│   ├── src/              # Source code
│   ├── .env.local        # Local env variables
│   └── package.json      # Dependencies
├── output/               # Generated files
│   └── {session_hash}/   # Session-specific files
│       ├── html/         # Generated HTML files
│       ├── pdf/          # Generated PDF files
│       ├── www/          # Generated logs
│       └── metadata.json # Session metadata
├── schemas/              # Document schemas
├── templates/            # HTML templates
├── users.db              # SQLite database for users
└── requirements.txt      # Python dependencies
```

## Development and Production

### Development
During development, you can run the backend and frontend separately:

```bash
# Backend
uvicorn api:app --reload --port 8000

# Frontend (in dashboard directory)
cd dashboard
npm run dev
```

### Production
For production, build the dashboard and serve it through the FastAPI app:

```bash
# Build dashboard
./build-dashboard.sh

# Run server
uvicorn api:app --host 0.0.0.0 --port 8000
```

## Troubleshooting

### Authentication Issues
- Check if the API key matches between backend and frontend
- Verify JWT token expiration and validity
- Check browser console for authentication errors

### File Serving Issues
- Ensure the API has proper permissions to read files
- Check that session directories exist and contain expected files
- Verify file paths in requests match the expected structure

### User Management Issues
- Check if the users database file is writable
- Verify the JWT secret is consistent
- Check role-based access control for admin endpoints