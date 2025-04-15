# DocTypeGen API Documentation

## Overview

The DocTypeGen API provides a RESTful interface to all document processing functionality. It is built using FastAPI and provides comprehensive endpoint documentation via Swagger UI.

## Base URL

```
http://localhost:8000/api
```

## Authentication

The API supports two authentication methods:

### API Key Authentication

Include the API key in the request header:

```
X-API-Key: your_api_key_here
```

### JWT Authentication

1. Obtain a JWT token by logging in:

```http
POST /api/auth/login
Body: {
  "username": "your_username",
  "password": "your_password"
}
```

2. Include the token in the Authorization header:

```
Authorization: Bearer your_jwt_token_here
```

## Endpoints

### Session Management

#### Get Current Session Status

```http
GET /api/status
```

Returns the current session status, including session hash, document type, and last operation.

#### Activate Session

```http
POST /api/sessions/{session_hash}/activate
```

Activates a specific session by hash.

#### List Sessions

```http
GET /api/sessions
```

Returns a list of all available sessions.

#### Get Session Details

```http
GET /api/sessions/{session_hash}
```

Returns detailed information about a specific session.

### Command Execution

#### List Available Commands

```http
GET /api/commands
```

Returns a list of all available commands.

#### Import File by Path

```http
POST /api/run/import
Body: {
  "file_path": "path/to/your/file.xlsx"
}
```

Imports a file from the specified path.

#### Import Uploaded File

```http
POST /api/run/import-upload
Body: multipart/form-data with file field
```

Imports an uploaded file.

#### Validate Data

```http
POST /api/run/validate
```

Validates the data in the current session against schemas.

#### Generate Field Mapping

```http
POST /api/run/map
```

Generates a field mapping for the current session.

#### Update Field Mapping

```http
POST /api/run/map
Body: {
  "field_updates": {
    "column_name": {
      "type": "FIELD_TYPE",
      "validate_type": "VALIDATION_TYPE",
      "required": true,
      "description": "Field description"
    }
  }
}
```

Updates the field mapping for the current session.

#### Delete Field Mapping

```http
POST /api/run/delete_mapping
```

Deletes the field mapping for the current session.

#### Generate HTML Documents

```http
POST /api/run/html
```

Generates HTML documents for the current session.

#### Generate PDF Documents

```http
POST /api/run/pdf
```

Generates PDF documents for the current session.

#### Resolve Lookups

```http
POST /api/run/lookup
```

Resolves lookups for the current session.

#### Get Lookup Exceptions

```http
GET /api/lookups/exceptions
Query Parameters:
  status: Filter by status (e.g., "pending", "matched", "exception")
  type: Filter by lookup type
```

Returns a list of lookup exceptions.

#### Resolve Lookup Exception

```http
POST /api/lookups/exceptions/{exception_id}/resolve
Body: {
  "resolution_type": "MANUAL_MATCH",
  "match_value": "matched_value"
}
```

Resolves a specific lookup exception.

#### Get Entities for Creation

```http
GET /api/lookups/entities-for-creation
```

Returns a list of entities that need to be created.

#### Create Entity

```http
POST /api/entities/create
Body: {
  "entity_type": "ENTITY_TYPE",
  "entity_data": {
    "field1": "value1",
    "field2": "value2"
  }
}
```

Creates a new entity.

#### Sync to Tenant Database

```http
POST /api/run/command
Body: {
  "command": "sync_tenant_db",
  "args": {}
}
```

Syncs data to tenant databases.

#### Transfer to S3

```http
POST /api/run/command
Body: {
  "command": "transfer_to_s3",
  "args": {}
}
```

Transfers files to S3 storage.

### File Access

#### Serve HTML File

```http
GET /api/files/{session_hash}/html/{filename}
```

Serves an HTML file from the session's html directory.

#### Serve PDF File

```http
GET /api/files/{session_hash}/pdf/{filename}
```

Serves a PDF file from the session's pdf directory.

#### Serve Log File

```http
GET /api/files/{session_hash}/logs/{filename}
```

Serves a log file from the session's logs directory.

#### List Files in Directory

```http
GET /api/files/{session_hash}/list/{directory}
```

Lists files in a specific directory of the session.

#### Download Session as ZIP

```http
GET /api/files/{session_hash}/zip
```

Creates and serves a ZIP file of all files in the session directory.

### User Management

#### List Users

```http
GET /api/users
```

Returns a list of all users.

#### Create User

```http
POST /api/users
Body: {
  "username": "new_username",
  "password": "new_password",
  "role": "user"
}
```

Creates a new user.

#### Update User

```http
PUT /api/users/{user_id}
Body: {
  "username": "updated_username",
  "password": "updated_password",
  "role": "admin"
}
```

Updates an existing user.

#### Delete User

```http
DELETE /api/users/{user_id}
```

Deletes a user.

## Response Format

Most API endpoints return responses in the following format:

```json
{
  "success": true,
  "command": "command_name",
  "result": {
    // Command-specific result data
  }
}
```

Or in case of an error:

```json
{
  "success": false,
  "error": "Error message"
}
```

## Error Handling

The API uses standard HTTP status codes:

- 200: Success
- 400: Bad Request (invalid input)
- 401: Unauthorized (authentication required)
- 403: Forbidden (insufficient permissions)
- 404: Not Found (resource not found)
- 500: Internal Server Error

Error responses include a detailed error message in the response body.

## Swagger Documentation

The API provides comprehensive documentation via Swagger UI, available at:

```
http://localhost:8000/docs
```

This interactive documentation allows you to:

- Browse all available endpoints
- See request and response schemas
- Test endpoints directly from the browser
- Authenticate and use secured endpoints
