# User Management Documentation

This document provides comprehensive details about the user management system in the Document Processing System, including authentication, authorization, and user administration through the CLI.

## Overview

The Document Processing System includes a user management system that allows administrators to create and manage users who can access the dashboard and API. Users are stored in a SQLite database with secure password hashing and role-based access control.

## User Roles

The system supports two user roles:

1. **admin** - Administrators have full access to all system features, including user management, document processing, and system configuration.
2. **user** - Standard users have limited access to features and may be restricted from certain operations based on configuration.

## User Properties

Each user in the system has the following properties:

- **Username**: Unique identifier for the user
- **Password**: Securely hashed using industry-standard algorithms
- **Role**: Either 'admin' or 'user'
- **Status**: Active or inactive
- **Created Date**: When the user was created
- **Last Login**: When the user last logged in

## Managing Users through the CLI

The Document Processing System provides a comprehensive set of CLI commands for managing users. These commands are available through the `user` command group.

### Available Commands

#### Adding a New User

```bash
python cli.py user add <username> <password> [--role ROLE]
```

**Arguments:**
- `username`: Username for the new user (required)
- `password`: Password for the new user (required)
- `--role`: Role for the new user, either 'user' or 'admin' (default: 'user')

**Example:**
```bash
python cli.py user add john.doe password123 --role admin
```

#### Listing All Users

```bash
python cli.py user list
```

This command displays a table of all users in the system, including their username, role, status, creation date, and last login time.

#### Changing a User's Password

```bash
python cli.py user password <username> <new_password>
```

**Arguments:**
- `username`: Username of the user to update (required)
- `new_password`: New password for the user (required)

**Example:**
```bash
python cli.py user password john.doe new_password123
```

#### Changing a User's Role

```bash
python cli.py user role <username> <new_role>
```

**Arguments:**
- `username`: Username of the user to update (required)
- `new_role`: New role for the user, either 'user' or 'admin' (required)

**Example:**
```bash
python cli.py user role john.doe admin
```

#### Activating or Deactivating a User

```bash
python cli.py user status <username> <is_active>
```

**Arguments:**
- `username`: Username of the user to update (required)
- `is_active`: New status for the user, True for active, False for inactive (required)

**Example:**
```bash
python cli.py user status john.doe True
```

#### Deleting a User

```bash
python cli.py user delete <username> [--force]
```

**Arguments:**
- `username`: Username of the user to delete (required)
- `--force, -f`: Force deletion without confirmation (default: False)

**Example:**
```bash
python cli.py user delete john.doe
```

## Password Security

The user management system employs secure password hashing with salt to protect user credentials. Passwords are never stored in plain text and are securely hashed using industry-standard algorithms.

When a user's password is changed, the system automatically generates a new salt and hash for the new password.

## Authentication Database

User information is stored in an SQLite database file located at `data/auth.db`. This file is created automatically when the first user is added to the system.

The database schema includes the following tables:
- `users`: Stores user information, including username, password hash, salt, role, status, and timestamps
- `login_attempts`: Tracks login attempts, including successful and failed attempts, for security auditing

## Troubleshooting

### Common Issues

1. **User already exists**
   - If you attempt to create a user with a username that already exists, you'll receive an error message. Use a different username or delete the existing user first.

2. **User not found**
   - If you attempt to modify a user that doesn't exist, you'll receive an error message. Check the username and try again.

3. **Invalid role**
   - If you attempt to assign a role other than 'user' or 'admin', you'll receive an error message. Use one of the supported roles.

### Reset Admin Password

If you've forgotten the admin password, you can reset it using the CLI:

```bash
python cli.py user password admin new_password
```

If that doesn't work, you can manually reset the password by creating a new user with the admin role:

```bash
python cli.py user add new_admin new_password --role admin
```

## Best Practices

1. **Use Strong Passwords**
   - Ensure all users, especially administrators, use strong, unique passwords.

2. **Regular Password Changes**
   - Periodically change passwords, especially for administrative accounts.

3. **User Audit**
   - Regularly audit the user list to ensure only authorized users have access to the system.

4. **Principle of Least Privilege**
   - Assign the least privileged role necessary for each user. Only give admin privileges to users who absolutely need them.

5. **Deactivate Instead of Delete**
   - When a user no longer needs access, consider deactivating their account instead of deleting it to maintain audit history.
