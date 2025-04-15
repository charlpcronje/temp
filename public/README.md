# Document Processing System

A complete system for processing CSV/Excel files into HTML/PDF documents with a modern React dashboard.

## Features

- 🔐 Authentication with role-based access control
- 🌗 Dark/light mode toggle
- 📊 Dashboard with session overview
- 📁 Session management with renaming and filtering
- 📤 File upload with drag and drop
- 🔄 Step-by-step processing workflow
- 📋 Log viewer for HTML/PDF outputs
- 👥 User management for administrators
- ⚙️ User settings and preferences
- 📱 Fully responsive design

## Project Structure

```
/
├── api.py                # FastAPI backend 
├── cli.py                # Command-line interface
├── commands.py           # Command registry
├── config/               # Configuration files
├── core/                 # Core business logic
├── dashboard/            # React dashboard
│   ├── public/           # Static assets
│   ├── src/              # Source code
│   ├── .env.development  # Dev environment variables
│   ├── .env.production   # Prod environment variables
│   └── package.json      # Dependencies
├── schemas/              # Document schemas
├── templates/            # HTML templates
│   ├── html/             # Document templates
│   ├── logs/             # Log templates
│   └── assets/           # Shared assets
└── requirements.txt      # Python dependencies
```

## Installation

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup

1. Install Python dependencies:

```bash
pip install -r requirements.txt
```

2. Create a configuration file in the `config` directory:

```bash
# config/dev.json
{
  "application": {
    "name": "Document Generator System",
    "version": "1.1.0"
  },
  "api": {
    "base_url": "http://localhost:8000",
    "auth_enabled": true,
    "auth_token": "your-secret-api-key"
  },
  # ... other settings ...
}
```

3. Run the API server:

```bash
uvicorn api:app --reload --port 8000
```

### Dashboard Setup

1. Navigate to the dashboard directory:

```bash
cd dashboard
```

2. Install dependencies:

```bash
npm install
# or
yarn install
```

3. Configure environment variables:

Create a `.env.local` file based on `.env.development` to override settings:

```
VITE_API_BASE_URL=http://localhost:8000
VITE_API_TIMEOUT=30000
VITE_USE_JWT_AUTH=true
# Or if using API key authentication:
# VITE_USE_JWT_AUTH=false
# VITE_API_KEY=your-secret-api-key
```

4. Start the development server:

```bash
npm run dev
# or
yarn dev
```

5. Build for production:

```bash
npm run build
# or
yarn build
```

## API Authentication Options

The system supports two authentication methods:

### 1. JWT Authentication (Default)

- Users log in with username/password
- Server returns a JWT token
- Token is stored in localStorage and sent with requests

### 2. API Key Authentication

- Static API key configured in backend and frontend
- All requests use the same API key
- No user-specific permissions

To configure API key authentication:

1. Set `auth_enabled` to `true` and specify `auth_token` in `config/dev.json`
2. Set `VITE_USE_JWT_AUTH=false` and `VITE_API_KEY=your-api-key` in dashboard env file

## Configuration Options

### Backend Config (config/dev.json)

- `application`: Basic application info
- `api`: API settings and authentication
- `documents_types`: Supported document types
- `html`: HTML generation settings
- `pdf`: PDF generation settings
- `database`: Database connection options
- `storage`: File storage configuration
- `logging`: Logging settings

### Dashboard Config (.env files)

- `VITE_API_BASE_URL`: API server URL
- `VITE_API_TIMEOUT`: Request timeout in milliseconds
- `VITE_USE_JWT_AUTH`: Whether to use JWT authentication
- `VITE_API_KEY`: API key for non-JWT authentication
- `VITE_MAX_FILE_SIZE`: Maximum upload file size
- `VITE_ACCEPTED_FILE_TYPES`: Allowed file extensions
- `VITE_DEFAULT_THEME`: Default color theme (light/dark/system)
- `VITE_ENABLE_USER_MANAGEMENT`: Enable user management features

## Production Deployment

### Building the Dashboard

```bash
cd dashboard
npm run build
# or
yarn build
```

This creates a `dist` directory with optimized static files.

### Serving the Application

The FastAPI application is configured to serve the dashboard from the `dashboard/dist` directory. 

1. Build the dashboard as described above
2. Configure your production environment (config/prod.json)
3. Run the API server:

```bash
uvicorn api:app --host 0.0.0.0 --port 8000
```

### Using a Production Web Server

For production, it's recommended to use a proper web server like Nginx or Apache.

Example Nginx configuration:

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Default Users

On first run, a default admin user is created:
- Username: `admin`
- Password: `admin`

**Important**: Change the default password immediately after first login.