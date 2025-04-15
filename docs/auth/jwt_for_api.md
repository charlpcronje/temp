# Authentication System Documentation

This document explains how to set up and use the authentication system for the Document Processing System.

## Overview

The authentication system provides:
- User management via CLI commands
- API protection with JWT tokens
- Role-based access control (admin/user roles)

## Files and Structure

- `core/auth/auth_db_manager.py` - User database operations
- `core/auth/jwt_auth.py` - JWT token generation and validation
- User management commands in `commands.py`
- Authentication endpoints in `api.py`

## Configuration

Add the following to your config files (e.g., `config/dev.json`):

```json
{
  "api": {
    "jwt_secret": "your-secret-key-change-this-in-production",
    "jwt_expiration_hours": 24,
    "auth_enabled": true
  }
}
```

The `auth.db` SQLite database will be created automatically in your project root directory.

## CLI Commands

### Adding a New User

```bash
python cli.py user add USERNAME --password PASSWORD --role ROLE
```

- `USERNAME`: Required username
- `PASSWORD`: Optional. If not provided, you'll be prompted to enter it securely
- `--role` or `-r`: Optional role (default: "user", alternative: "admin")

Example:
```bash
python cli.py user add admin --role admin
```

The CLI will prompt you to enter a password securely.

### Listing Users

```bash
python cli.py user list
```

This will display all users in a table format with their ID, username, role, creation date, last login, and status.

### Changing User Password

```bash
python cli.py user password USERNAME --password NEW_PASSWORD
```

- `USERNAME`: Required username
- `--password` or `-p`: Optional new password. If not provided, you'll be prompted to enter it securely

### Changing User Role

```bash
python cli.py user role USERNAME ROLE
```