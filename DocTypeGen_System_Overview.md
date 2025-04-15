# DocTypeGen System Overview

This document provides a comprehensive overview of the DocTypeGen system, its architecture, components, and workflows. It serves as an onboarding guide for anyone working on the system.

## System Purpose

DocTypeGen is a document processing system that:
1. Imports spreadsheet data (CSV/Excel)
2. Validates data against predefined schemas
3. Maps columns to field types
4. Generates HTML and PDF documents
5. Resolves lookups against external data
6. Creates missing entities
7. Syncs data to tenant databases
8. Transfers files to S3 storage

## Core Architecture

### Session Management

#### Sessions and Hashes
- Each processing job is a "session" identified by a unique hash
- Session hashes are used in file paths, database names, and API endpoints
- The system maintains two key files:
  - `status.json`: Tracks the current active session
  - `sessions.json`: Tracks all sessions and their last operations

#### Status.json
```json
{
  "last_updated": "2023-06-01T12:00:00",
  "current_state": {
    "hash": "8e1db936f9717465ff2b2bed398893177404e47ceb6142a6afb117efcd0306d8",
    "last_operation": "VALIDATE_DATA",
    "document_type": "SHAREHOLDER_REGISTER",
    "imported_file": "path/to/file.csv",
    "output_folder": "output/8e1db936f9717465ff2b2bed398893177404e47ceb6142a6afb117efcd0306d8",
    "sqlite_db_file": "output/8e1db936f9717465ff2b2bed398893177404e47ceb6142a6afb117efcd0306d8/data.db"
  }
}
```

#### Sessions.json
```json
{
  "8e1db936f9717465ff2b2bed398893177404e47ceb6142a6afb117efcd0306d8": {
    "last_updated": "2023-06-01T12:00:00",
    "last_operation": "VALIDATE_DATA",
    "document_type": "SHAREHOLDER_REGISTER",
    "output_folder": "output/8e1db936f9717465ff2b2bed398893177404e47ceb6142a6afb117efcd0306d8"
  },
  "866c661a99cd0e00c2c5ac9f1f9cf7c39bc8b656e6f390cc686b899d6dcb45d0": {
    "last_updated": "2023-05-30T10:30:00",
    "last_operation": "GENERATE_HTML",
    "document_type": "BOARD_MINUTES",
    "output_folder": "output/866c661a99cd0e00c2c5ac9f1f9cf7c39bc8b656e6f390cc686b899d6dcb45d0"
  }
}
```

### File Structure

#### Output Directory
- Each session has its own directory under `output/[session_hash]/`
- Contains:
  - `data.db`: SQLite database with imported data
  - `metadata.json`: Session metadata
  - `mapping.json`: Field mappings
  - HTML files: Generated documents
  - PDF files: Generated documents
  - Log files: Processing logs

#### Config Directory
- Contains schema definitions and templates
- `config/schemas/`: JSON schema files defining document types
- `config/templates/`: HTML templates for document generation

### Database Structure
- Each session has its own SQLite database (`data.db`)
- Main tables:
  - `imported_[hash]`: Raw imported data
  - `generated_imported_[hash]`: Processed data
  - `tenant_lookup_imported_[hash]`: Lookup data

## Document Schemas

### Schema Definition
- Schemas define document types and their field requirements
- Located in `config/schemas/[document_type].json`
- Each schema defines:
  - Field types (e.g., SHAREHOLDER_FULL_NAME, DOMICILE_CODE)
  - Validation rules (regex, required, etc.)
  - Max matches (how many columns can map to this type)

Example schema:
```json
{
  "name": "SHAREHOLDER_REGISTER",
  "description": "Shareholder Register Document",
  "fields": [
    {
      "name": "SHAREHOLDER_FULL_NAME",
      "description": "Full name of shareholder",
      "validation_type": "REGEX",
      "regex": "^[A-Za-z\\s\\/]+$",
      "required": true,
      "max_matches": 1
    },
    {
      "name": "DOMICILE_CODE",
      "description": "Domicile country code",
      "validation_type": "REGEX",
      "regex": "^[A-Z]{2}$",
      "required": false,
      "max_matches": 1
    }
  ]
}
```

### Document Type Detection
- The system detects document type by matching schemas against columns
- Determines the best schema match based on column names and content
- Validation is based on content types, not column names

## Processing Workflow

### 1. Import Data
- Upload CSV or Excel file
- Parse file and create SQLite database
- Store raw data in `imported_[hash]` table
- Create session with unique hash

### 2. Validate & Map Data
- Validate data against schema requirements
- Map columns to field types
- Generate validation report
- Store mapping in `mapping.json`

### 3. Generate HTML
- Use mapped data and HTML templates
- Generate HTML documents for each row
- Store HTML files in session directory

### 4. Generate PDF (Optional)
- Convert HTML documents to PDF
- Store PDF files in session directory

### 5. Resolve Lookups
- Match data against external lookup tables
- Resolve references to external entities

### 6. Entity Creation (Optional)
- Create missing entities in external systems

### 7. Data Sync (Optional)
- Sync processed data to tenant database

### 8. Storage (Optional)
- Transfer files to S3 storage

## User Interfaces

### Web UI
- React-based frontend in `/public` directory
- Main components:
  - Dashboard: Overview of sessions
  - Workflow: Step-by-step processing interface
  - Sessions: List of all sessions
  - Logs: Processing logs and reports
  - Users: User management
  - Settings: System settings

#### Web UI Navigation
- All routes use the `/app/` prefix:
  - `/app/dashboard`: Main dashboard
  - `/app/workflow`: Processing workflow
  - `/app/sessions`: Session management
  - `/app/logs`: Log viewer
  - `/app/users`: User management
  - `/app/settings`: System settings

### CLI Interface
- Command-line interface for all operations
- Commands defined in `commands.py`
- Example: `python cli.py import --file data.csv`

### TUI Interface
- Text-based user interface
- Simplified version of the web UI

## API Endpoints

### Main Endpoints
- `/api/status`: Get current session status
- `/api/import`: Import data
- `/api/validate`: Validate data
- `/api/run/html`: Generate HTML
- `/api/run/pdf`: Generate PDF
- `/api/sessions/{session_hash}/activate`: Activate a session

### Session Management
- `/api/sessions`: List all sessions
- `/api/logs`: List all logs
- `/api/logs/{hash}`: Get log details

## Logging System

### Log Files
- Each operation generates HTML log files
- Log files are stored in the session directory
- Naming convention: `operation_[execution_id].html`
- Row-specific logs: `validate_row_[row_number].html`

### Log Viewer
- Web UI provides a log viewer
- Shows HTML, PDF, and log files for each session

## Code Organization

### Backend
- `api.py`: FastAPI application
- `commands.py`: Command definitions
- `cli.py`: Command-line interface
- `core/`: Core functionality
  - `importer.py`: Data import
  - `validator.py`: Data validation
  - `html_generator.py`: HTML generation
  - `pdf_generator.py`: PDF generation
  - `session.py`: Session management
  - `logger.py`: Logging system

### Frontend
- `public/`: React application
  - `src/`: Source code
    - `components/`: React components
    - `pages/`: Page components
    - `api/`: API client
    - `types/`: TypeScript types

## Development Guidelines

1. **Backend Stability**: Prioritize backend stability over frontend changes
2. **Methodical Approach**: Make one change at a time to identify issues
3. **Comprehensive Planning**: Plan changes before implementation
4. **Minimal Changes**: Make targeted fixes rather than extensive refactoring
5. **Schema Immutability**: Never edit schema files directly
6. **Error Handling**: Implement robust error handling for file operations
7. **Testing**: Write and run tests for all changes

## Common Issues and Solutions

### Session Activation
- Issue: "Session is not active or cannot be found"
- Solution: Use the activate_session command to activate the session

### Validation Errors
- Issue: Validation fails for valid data
- Solution: Check regex patterns and validation thresholds

### Mapping Issues
- Issue: Columns not showing in mapping
- Solution: Ensure all columns are retrieved from the database

### File Generation
- Issue: HTML/PDF generation fails
- Solution: Check templates and mapping file

## Utility Scripts

- `view_sessions.py`: View the contents of sessions.json
- `view_status.py`: View the contents of status.json
- `activate_session.py`: Activate a session by hash

