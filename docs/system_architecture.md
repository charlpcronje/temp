# DocTypeGen System Architecture

## Overview

DocTypeGen is an intelligent document processing system that imports spreadsheets, validates data against schemas, maps columns to field types, generates HTML/PDF documents, resolves lookups, creates entities, syncs data to tenant databases, and transfers files to S3 storage.

## System Components

### 1. Session Management

The session management system is responsible for:
- Creating and tracking processing sessions
- Maintaining state via `status.json`
- Creating output directories for each session
- Loading configuration based on environment

Key files:
- `core/session.py`: Handles session creation, activation, and status tracking
- `status.json`: Tracks the current active session
- `output/{session_hash}/metadata.json`: Stores session-specific metadata

### 2. Document Schemas

Schemas define document types and validation rules:
- Each schema represents a document type (e.g., payment_advice, statement)
- Schemas define field types, validation rules, and output templates
- Schemas are stored as JSON files in the `schemas/` directory

Example schema structure:
```json
{
  "type": "payment_advice",
  "template": "payment_advice.html",
  "output_doc_name": "{datetime}_{ID_NUMBER}_payment_advice_{REFERENCE}.{HTML|PDF}",
  "schema": {
    "FIELD_NAME": {
      "slug": ["FIELD_NAME", "ALTERNATIVE_NAME"],
      "validate_type": "REGEX",
      "regex": "^.{2,}$",
      "required": true,
      "description": "Description of the field"
    }
  }
}
```

### 3. Processing Workflow

The system follows a sequential workflow:

1. **Import**: 
   - Imports CSV/Excel files into SQLite database
   - Creates a session hash based on file content
   - Sets up output directory structure

2. **Validation**:
   - Detects document type by matching schemas against columns
   - Validates data against schema rules
   - Generates validation reports

3. **Mapping**:
   - Creates a mapping between spreadsheet columns and schema fields
   - Allows manual adjustment of mappings
   - Validates mappings against schema requirements

4. **HTML Generation**:
   - Uses Jinja2 templates to generate HTML documents
   - Applies mapped data to templates
   - Creates one HTML file per row in the database

5. **PDF Generation**:
   - Converts HTML files to PDF using WeasyPrint or wkhtmltopdf
   - Maintains consistent styling and layout
   - Stores PDFs in the session output directory

6. **Lookup Resolution**:
   - Matches document data against external databases
   - Resolves references to entities (e.g., users, accounts)
   - Handles exceptions for unmatched records

7. **Entity Creation**:
   - Creates new entities based on document data
   - Updates existing entities with new information
   - Manages entity relationships

8. **Tenant Database Sync**:
   - Syncs processed data to tenant databases
   - Maintains data consistency across systems
   - Handles sync errors and retries

9. **S3 Transfer**:
   - Transfers generated files to S3 storage
   - Organizes files by session and document type
   - Updates file status in the database

### 4. Interfaces

The system provides multiple interfaces:

#### Web UI
- React-based dashboard for managing the entire workflow
- Visual representation of validation results
- Interactive mapping editor
- Document preview and download
- User management and authentication

#### CLI
- Command-line interface for all operations
- Scriptable for automation
- Detailed logging and error reporting
- User management commands

#### REST API
- FastAPI-based REST endpoints
- Authentication via API keys or JWT
- Comprehensive endpoint documentation via Swagger UI
- Supports all workflow operations

#### TUI (Terminal UI)
- Text-based interface for terminal environments
- Interactive menus and forms
- Progress indicators and status updates

### 5. Storage and Output

The system organizes outputs by session:

```
output/
└── {session_hash}/
    ├── html/             # Generated HTML documents
    ├── pdf/              # PDF versions
    ├── www/              # Web dashboard
    │   ├── index.html    # Session dashboard
    │   ├── logs/         # HTML logs
    │   └── assets/       # CSS, JS, images
    ├── logs/             # Log files
    ├── mappings/         # Field mapping files
    ├── reports/          # Audit reports
    ├── data.db           # Session SQLite database
    └── metadata.json     # Session metadata
```

## Data Flow

1. User uploads a spreadsheet file through one of the interfaces
2. System creates a session and imports the file into SQLite
3. Validation process detects document type and validates data
4. User reviews and adjusts field mappings if needed
5. System generates HTML documents based on templates
6. HTML documents are converted to PDF
7. Lookups are resolved against external data sources
8. New entities are created if needed
9. Data is synced to tenant databases
10. Files are transferred to S3 storage
11. User can access all generated files and reports

## Extension Points

The system is designed for extensibility:

1. **New Document Types**: Add new schemas to the `schemas/` directory
2. **Custom Validation Types**: Create new validation classes in `core/validator/`
3. **Template Customization**: Modify or add templates in `templates/html/`
4. **Additional Interfaces**: Implement new interfaces using the core command structure
5. **Storage Backends**: Add support for different storage systems beyond S3

## Security Considerations

- User authentication and authorization
- API key management
- Input validation and sanitization
- Secure file handling
- Database connection security
- Tenant data isolation
