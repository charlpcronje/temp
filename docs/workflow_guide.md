# DocTypeGen Workflow Guide

This guide explains the step-by-step workflow for processing documents using DocTypeGen.

## Workflow Overview

The DocTypeGen system follows a sequential workflow:

1. **Import**: Upload and import a spreadsheet file
2. **Validate & Map**: Validate data and map columns to field types
3. **HTML Generation**: Generate HTML documents from templates
4. **PDF Generation**: Convert HTML documents to PDF
5. **Lookup Resolution**: Match records to external data sources
6. **Entity Creation**: Create new entities based on document data
7. **Data Sync**: Sync data to tenant databases
8. **Storage**: Transfer files to S3 storage

## Detailed Steps

### Step 1: Import

This step imports a spreadsheet file (CSV or Excel) into the system.

#### Web UI
1. Navigate to the Upload page
2. Drag and drop a file or click to browse
3. Click "Upload and Import"

#### CLI
```bash
python cli.py import --file_path path/to/your/file.xlsx
```

#### API
```http
POST /api/run/import
Body: { "file_path": "path/to/your/file.xlsx" }
```

or

```http
POST /api/run/import-upload
Body: multipart/form-data with file field
```

**What happens:**
- The file is validated for format and structure
- A session hash is generated based on the file content
- Data is imported into a SQLite database
- A session directory is created in the output folder
- The status.json file is updated with the session information

### Step 2: Validate & Map

This step validates the imported data against schemas and maps columns to field types.

#### Web UI
1. After import, you'll be automatically redirected to the Validation page
2. Review the detected document type and validation results
3. Adjust field mappings if needed
4. Click "Continue to HTML Generation"

#### CLI
```bash
python cli.py validate
python cli.py map
```

#### API
```http
POST /api/run/validate
POST /api/run/map
```

**What happens:**
- The system compares the imported data against available schemas
- The best matching document type is detected
- Data is validated against the schema rules
- A mapping file is generated to link columns to field types
- Validation results are displayed with success rates and error details

### Step 3: HTML Generation

This step generates HTML documents from templates using the validated data.

#### Web UI
1. After validation, you'll be automatically redirected to the HTML Generation page
2. Review the template that will be used
3. Click "Generate HTML"
4. View and download generated HTML files

#### CLI
```bash
python cli.py html
```

#### API
```http
POST /api/run/html
```

**What happens:**
- The system loads the template specified in the schema
- For each row in the database, a HTML document is generated
- Field values are inserted into the template using Jinja2
- Generated files are stored in the session's html directory
- Metadata about generated files is stored in the database

### Step 4: PDF Generation

This step converts the generated HTML documents to PDF.

#### Web UI
1. After HTML generation, you'll be automatically redirected to the PDF Generation page
2. Click "Generate PDF"
3. View and download generated PDF files

#### CLI
```bash
python cli.py pdf
```

#### API
```http
POST /api/run/pdf
```

**What happens:**
- The system loads each HTML file
- HTML is converted to PDF using WeasyPrint or wkhtmltopdf
- Generated PDFs are stored in the session's pdf directory
- Metadata about generated files is stored in the database

### Step 5: Lookup Resolution

This step matches records to external data sources.

#### Web UI
1. After PDF generation, you'll be automatically redirected to the Lookup Resolution page
2. Review lookup results and exceptions
3. Resolve exceptions manually if needed
4. Click "Continue"

#### CLI
```bash
python cli.py lookup
```

#### API
```http
POST /api/run/lookup
```

**What happens:**
- The system attempts to match key fields (e.g., ID numbers) to external databases
- Successful matches are recorded
- Exceptions are flagged for manual resolution
- Lookup results are stored in the database

### Step 6: Entity Creation

This step creates new entities based on document data.

#### Web UI
1. After lookup resolution, you'll be automatically redirected to the Entity Creation page
2. Review entities to be created
3. Click "Create Entities"

#### CLI
```bash
python cli.py entity
```

#### API
```http
POST /api/run/entity
```

**What happens:**
- The system identifies records that require new entity creation
- New entities are created in the system
- Entity creation results are stored in the database

### Step 7: Data Sync

This step syncs processed data to tenant databases.

#### Web UI
1. After entity creation, you'll be automatically redirected to the Data Sync page
2. Click "Sync Data"
3. Review sync results

#### CLI
```bash
python cli.py sync
```

#### API
```http
POST /api/run/sync
```

**What happens:**
- The system connects to tenant databases
- Processed data is synced to the appropriate tables
- Sync results and errors are recorded

### Step 8: Storage

This step transfers generated files to S3 storage.

#### Web UI
1. After data sync, you'll be automatically redirected to the Storage page
2. Click "Transfer Files"
3. Review transfer results

#### CLI
```bash
python cli.py transfer
```

#### API
```http
POST /api/run/transfer
```

**What happens:**
- The system connects to S3
- Generated files are uploaded to the appropriate buckets
- Transfer results and errors are recorded

## Session Management

### Activating an Existing Session

#### Web UI
1. Navigate to the Sessions page
2. Click on a session
3. Click "Continue Processing"

#### CLI
```bash
python cli.py activate_session SESSION_HASH
```

#### API
```http
POST /api/sessions/{session_hash}/activate
```

### Viewing Session Outputs

#### Web UI
1. Navigate to the Sessions page
2. Click on a session
3. Browse the HTML, PDF, and log files

#### CLI
```bash
python cli.py list_files SESSION_HASH
```

#### API
```http
GET /api/sessions/{session_hash}/files
```

## Troubleshooting

### Common Issues

1. **"No session found" error**
   - Check if status.json exists and contains valid session information
   - Try activating a session explicitly

2. **Validation failures**
   - Review the validation errors in the UI or logs
   - Check if the schema matches the document type
   - Adjust field mappings manually

3. **HTML/PDF generation issues**
   - Verify that templates exist and are correctly formatted
   - Check for missing required fields in the data
   - Ensure PDF generation tools are properly installed

4. **Lookup/Entity creation failures**
   - Check connection to external databases
   - Verify that lookup fields contain valid data
   - Review exception logs for specific errors

5. **Data sync/S3 transfer issues**
   - Verify connection credentials
   - Check permissions for databases and S3 buckets
   - Review error logs for specific failures

### Logs and Reports

- HTML logs: `output/{session_hash}/www/logs/`
- Session dashboard: `output/{session_hash}/www/index.html`
- Application logs: `logs/app.log`
- Database: `output/{session_hash}/data.db`
