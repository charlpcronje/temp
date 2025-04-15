# API Documentation and Configuration Files

## API Documentation

The Document Processing System provides a RESTful API for remote access to all document processing features. The API is built with FastAPI and offers robust endpoints for each processing step.

### API Overview

- **Base URL**: `http://localhost:8000` (default)
- **Content Type**: `application/json` for request/response bodies
- **Authentication**: API key authentication via `X-API-Key` header (optional, configurable)
- **Documentation**: Interactive API docs available at `/docs` endpoint

### Authentication

Authentication is optional and configurable. When enabled, include your API key in the request header:

```
X-API-Key: your-api-key-here
```

Authentication settings are controlled in the configuration file:

```json
{
  "api": {
    "auth_enabled": true,
    "auth_token": "your-secret-key"
  }
}
```

### API Endpoints

#### 1. List Available Commands

Returns a list of all available commands with descriptions.

- **URL**: `/commands`
- **Method**: GET
- **Authentication**: Optional

**Response Example**:
```json
{
  "import": {
    "func": "import_file",
    "args": ["file_path"],
    "description": "Import a CSV or Excel file into SQLite."
  },
  "validate": {
    "func": "validate_data",
    "args": [],
    "description": "Validate the active session and detect document type."
  },
  "map": {
    "func": "generate_mapping_file",
    "args": [],
    "description": "Generate editable field-type mapping for this session."
  },
  "html": {
    "func": "generate_html_files",
    "args": [],
    "description": "Generate HTML files from mapped, validated data."
  },
  "pdf": {
    "func": "generate_pdfs",
    "args": [],
    "description": "Generate PDFs from HTML templates."
  },
  "all": {
    "description": "Run all steps in sequence: import, validate, map, html, pdf."
  }
}
```

#### 2. Get Current Session Status

Returns status information for the current session.

- **URL**: `/status`
- **Method**: GET
- **Authentication**: Optional

**Response Example**:
```json
{
  "active_session": true,
  "session_hash": "ce65e00a455ca83cf53c6a687daa45ff52c0cd6732deae7c682beb3e5b60bbb3",
  "session_dir": "output/ce65e00a455ca83cf53c6a687daa45ff52c0cd6732deae7c682beb3e5b60bbb3"
}
```

#### 3. Import File by Path

Import a file by providing a path on the server.

- **URL**: `/run/import`
- **Method**: POST
- **Authentication**: Optional
- **Form Parameters**:
  - `file_path`: Path to the file on the server (required)

**Request Example**:
```
POST /run/import
Content-Type: application/x-www-form-urlencoded

file_path=/path/to/data.csv
```

**Response Example**:
```json
{
  "success": true,
  "command": "import",
  "result": {
    "hash": "ce65e00a455ca83cf53c6a687daa45ff52c0cd6732deae7c682beb3e5b60bbb3",
    "file_path": "/path/to/data.csv",
    "table_name": "imported_ce65e00a45",
    "num_rows": 1000,
    "columns": ["column1", "column2", "column3"],
    "db_path": "output/ce65e00a455ca83cf53c6a687daa45ff52c0cd6732deae7c682beb3e5b60bbb3/data.db",
    "session_dir": "output/ce65e00a455ca83cf53c6a687daa45ff52c0cd6732deae7c682beb3e5b60bbb3"
  }
}
```

#### 4. Import Uploaded File

Import a file uploaded directly to the API.

- **URL**: `/run/import-upload`
- **Method**: POST
- **Authentication**: Optional
- **Content-Type**: `multipart/form-data`
- **Form Parameters**:
  - `file`: File to upload (required)

**Request Example**:
```
POST /run/import-upload
Content-Type: multipart/form-data
--boundary
Content-Disposition: form-data; name="file"; filename="data.csv"
Content-Type: text/csv

(file content)
--boundary--
```

**Response Example**:
```json
{
  "success": true,
  "command": "import-upload",
  "result": {
    "hash": "ce65e00a455ca83cf53c6a687daa45ff52c0cd6732deae7c682beb3e5b60bbb3",
    "file_path": "/tmp/uploaded_file.csv",
    "table_name": "imported_ce65e00a45",
    "num_rows": 1000,
    "columns": ["column1", "column2", "column3"],
    "db_path": "output/ce65e00a455ca83cf53c6a687daa45ff52c0cd6732deae7c682beb3e5b60bbb3/data.db",
    "session_dir": "output/ce65e00a455ca83cf53c6a687daa45ff52c0cd6732deae7c682beb3e5b60bbb3"
  }
}
```

#### 5. Run Any Command

Generic endpoint to run any of the system commands.

- **URL**: `/run/{command}`
- **Method**: POST
- **Authentication**: Optional
- **Path Parameters**:
  - `command`: Name of the command to run (required)
- **Request Body**: JSON object with command arguments

**Request Example for validate**:
```json
POST /run/validate
Content-Type: application/json

{}
```

**Response Example**:
```json
{
  "success": true,
  "command": "validate",
  "result": {
    "validation_results": {
      "schema_name": "payment_advice_schema",
      "document_type": "payment_advice",
      "match_score": 95.5,
      "total_rows": 1000,
      "valid_rows": 980,
      "invalid_rows": 20,
      "success_rate": 98.0
    }
  }
}
```

#### 6. Run Generic Command

Execute any available command.

- **URL**: `/run/{command}`
- **Method**: POST
- **Authentication**: Optional
- **Path Parameters**:
  - `command`: Name of the command to run
- **Request Body**: JSON object with command parameters

**Request Example**:
```json
{
  "file_path": "/path/to/file.csv"
}
```

**Response Example**:
```json
{
  "success": true,
  "command": "import",
  "result": {
    "message": "File imported successfully",
    "rows_processed": 150
  }
}
```

#### 7. Resolve Lookups

Resolve lookups for generated documents, attempting to match records to database entities.

- **URL**: `/run/resolve_lookups`
- **Method**: POST
- **Authentication**: Optional
- **Request Body**: JSON object with session parameter (optional)

**Request Example**:
```json
{
  "session": null
}
```

**Response Example**:
```json
{
  "success": true,
  "command": "resolve_lookups",
  "result": {
    "resolved_count": 120,
    "unresolved_count": 5,
    "exception_count": 2,
    "session_hash": "ce65e00a455ca83cf53c6a687daa45ff52c0cd6732deae7c682beb3e5b60bbb3"
  }
}
```

#### 8. Get Lookup Exceptions

Get a list of lookup exceptions for the current session.

- **URL**: `/lookup/exceptions`
- **Method**: GET
- **Authentication**: Optional

**Response Example**:
```json
{
  "success": true,
  "exceptions": [
    {
      "id": 1,
      "document_id": "doc123",
      "lookup_field": "customer_id",
      "lookup_value": "12345",
      "error_message": "No matching record found",
      "created_at": "2023-03-25T12:34:56"
    },
    {
      "id": 2,
      "document_id": "doc456",
      "lookup_field": "account_number",
      "lookup_value": "ACC-789",
      "error_message": "Multiple matches found",
      "created_at": "2023-03-25T13:45:12"
    }
  ]
}
```

### Report Endpoints

The following endpoints provide access to the report generation and retrieval system.

#### 1. Generate Reports

Generate all reports for the current session.

- **URL**: `/report/generate`
- **Method**: POST
- **Authentication**: Optional
- **Request Body**: Empty or null

**Response Example**:
```json
{
  "success": true,
  "command": "report_generate",
  "result": {
    "report_id": "r-12345678",
    "session_hash": "ce65e00a455ca83cf53c6a687daa45ff52c0cd6732deae7c682beb3e5b60bbb3",
    "reports_generated": [
      "summary.html",
      "mapping.html",
      "verify.html",
      "exceptions.html"
    ],
    "pdf_reports": [
      "summary.pdf",
      "mapping.pdf",
      "verify.pdf",
      "exceptions.pdf"
    ]
  }
}
```

#### 2. Rerun Report

Re-run a previously generated report by its ID.

- **URL**: `/report/rerun`
- **Method**: POST
- **Authentication**: Optional
- **Request Body**: JSON object with report_id parameter

**Request Example**:
```json
{
  "report_id": "r-12345678"
}
```

**Response Example**:
```json
{
  "success": true,
  "command": "report_rerun",
  "result": {
    "report_id": "r-12345678",
    "session_hash": "ce65e00a455ca83cf53c6a687daa45ff52c0cd6732deae7c682beb3e5b60bbb3",
    "reports_generated": [
      "summary.html",
      "mapping.html",
      "verify.html",
      "exceptions.html"
    ],
    "pdf_reports": [
      "summary.pdf",
      "mapping.pdf",
      "verify.pdf",
      "exceptions.pdf"
    ]
  }
}
```

#### 3. List Reports

List all report runs with their status.

- **URL**: `/report/list`
- **Method**: GET
- **Authentication**: Optional

**Response Example**:
```json
{
  "success": true,
  "command": "report_list",
  "result": {
    "reports": [
      {
        "report_id": "r-12345678",
        "session_hash": "ce65e00a455ca83cf53c6a687daa45ff52c0cd6732deae7c682beb3e5b60bbb3",
        "created_at": "2023-03-25T14:30:00",
        "status": "complete",
        "report_files": [
          "summary.html",
          "mapping.html",
          "verify.html",
          "exceptions.html",
          "summary.pdf",
          "mapping.pdf",
          "verify.pdf",
          "exceptions.pdf"
        ]
      },
      {
        "report_id": "r-87654321",
        "session_hash": "ce65e00a455ca83cf53c6a687daa45ff52c0cd6732deae7c682beb3e5b60bbb3",
        "created_at": "2023-03-24T10:15:00",
        "status": "complete",
        "report_files": [
          "summary.html",
          "mapping.html",
          "verify.html",
          "exceptions.html",
          "summary.pdf",
          "mapping.pdf",
          "verify.pdf",
          "exceptions.pdf"
        ]
      }
    ]
  }
}
```

#### 4. Get Report HTML

Get an HTML report file by report ID and filename.

- **URL**: `/report/{report_id}/html/{filename}`
- **Method**: GET
- **Authentication**: Optional
- **Path Parameters**:
  - `report_id`: ID of the report
  - `filename`: Name of the HTML file (e.g., summary.html)

**Response**: HTML content

#### 5. Get Report PDF

Get a PDF report file by report ID and filename.

- **URL**: `/report/{report_id}/pdf/{filename}`
- **Method**: GET
- **Authentication**: Optional
- **Path Parameters**:
  - `report_id`: ID of the report
  - `filename`: Name of the PDF file (e.g., summary.pdf)

**Response**: PDF file

### Error Responses

All endpoints may return error responses in the following format:

```json
{
  "success": false,
  "command": "command_name",
  "error": "Error message describing what went wrong."
}
```

Common HTTP status codes:
- `400 Bad Request`: Invalid parameters or request body
- `401 Unauthorized`: Missing or invalid API key
- `404 Not Found`: Command or resource not found
- `500 Internal Server Error`: Server-side processing error

### Static Files Access

The API serves static files from the current session's output directory:

- **URL**: `/static/{file_path}`
- **Method**: GET
- **Parameters**:
  - `file_path`: Path to the file within the www directory

**Example**:
```
GET /static/dashboard.html
```

### Sample API Client (Python)

Here's a sample Python client for interacting with the API:

```python
import requests
import json

class DocumentProcessorClient:
    def __init__(self, base_url="http://localhost:8000", api_key=None):
        self.base_url = base_url
        self.headers = {"X-API-Key": api_key} if api_key else {}

    def list_commands(self):
        response = requests.get(f"{self.base_url}/commands", headers=self.headers)
        return response.json()

    def get_status(self):
        response = requests.get(f"{self.base_url}/status", headers=self.headers)
        return response.json()

    def import_file(self, file_path):
        data = {"file_path": file_path}
        response = requests.post(
            f"{self.base_url}/run/import", 
            data=data,
            headers=self.headers
        )
        return response.json()

    def upload_file(self, file_path):
        with open(file_path, "rb") as f:
            files = {"file": (file_path.split("/")[-1], f)}
            response = requests.post(
                f"{self.base_url}/run/import-upload",
                files=files,
                headers=self.headers
            )
        return response.json()

    def run_command(command_name: str, **kwargs) -> Any:
        """
        Execute a command from the registry with the given arguments.
        
        Args:
            command_name: The name of the command to execute
            **kwargs: Arguments to pass to the command
        
        Returns:
            The result of the command execution
        
        Raises:
            CommandNotFoundError: If command doesn't exist
            SessionRequiredError: If no active session exists for commands that need one
            CommandExecutionError: If command execution fails
        """
        if command_name not in COMMANDS:
            raise ValueError(f"Unknown command: {command_name}")
        
        if command_name == "all":
            return run_all_commands(**kwargs)
        
        command = COMMANDS[command_name]
        
        # Handle case where command might not have 'func' defined
        if 'func' not in command:
            raise ValueError(f"Command '{command_name}' has no implementation function")
            
        func = command["func"]
        
        # Special case for user management commands - they don't need a session
        if not command_name.startswith("user_"):
            # Ensure output directory exists for all commands except import
            if command_name != "import":
                session_hash = get_current_session()
                if not session_hash:
                    raise ValueError("No active session. Import a file first.")
                
                try:
                    create_output_dir(session_hash)
                except Exception as e:
                    raise RuntimeError(f"Failed to create output directory: {str(e)}")
        
        # Extract only the arguments needed by the function
        func_args = {k: v for k, v in kwargs.items() if k in command.get("args", [])}
        
        try:
            logger.info(f"Running command: {command_name}")
            result = func(**func_args)
            logger.info(f"Command {command_name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Error executing command {command_name}: {str(e)}")
            # Re-raise with more context
            raise RuntimeError(f"Command {command_name} failed: {str(e)}") from e


    def run_all_commands(**kwargs) -> Dict[str, Any]:
        """
        Run all commands in sequence.
        
        Args:
            **kwargs: Arguments for all commands
        
        Returns:
            Dict of results from each command
        """
        results = {}
        
        # First run import
        if "file_path" not in kwargs:
            raise ValueError("file_path is required for the import command")
        
        try:
            results["import"] = run_command("import", **kwargs)
        except Exception as e:
            logger.error(f"Import step failed: {e}")
            raise ValueError(f"Import step failed: {e}")
        
        # Then run the rest in sequence
        for cmd in ["validate", "map", "html", "pdf"]:
            try:
                results[cmd] = run_command(cmd)
            except Exception as e:
                logger.error(f"{cmd.capitalize()} step failed: {e}")
                results[cmd] = {"error": str(e), "success": False}
        
        return results


    def process_file(self, file_path, upload=False):
        """Run complete workflow for a file"""
        if upload:
            result = self.upload_file(file_path)
        else:
            result = self.import_file(file_path)
        
        if not result.get("success"):
            return result
        
        # Run remaining steps
        commands = ["validate", "map", "html", "pdf"]
        results = {}
        results["import"] = result
        
        for command in commands:
            result = self.run_command(command)
            results[command] = result
            if not result.get("success"):
                return results
                
        return results

# Usage example
if __name__ == "__main__":
    client = DocumentProcessorClient(api_key="your-api-key")
    result = client.process_file("/path/to/data.csv")
    print(json.dumps(result, indent=2))
```

## Configuration Files

The Document Processing System uses several configuration files to control its behavior. Here's a detailed documentation of each required configuration file.

### 1. Environment Configuration (.env)

The `.env` file contains environment variables that control the system's basic behavior.

**Location**: Root directory of the application
**Format**: Key-value pairs

**Example `.env` file**:
```
ENV=dev  # Options: dev, prod
DEBUG=true
```

**Available settings**:
- `ENV`: Environment to use (loads corresponding config file from config/ directory)
- `DEBUG`: Enable/disable debug mode

### 2. Main Configuration Files (config/*.json)

The main configuration files control various aspects of the system's behavior based on the environment.

**Location**: `config/dev.json` and `config/prod.json`
**Format**: JSON

**Example `config/dev.json`**:
```json
{
  "application": {
    "name": "Document Generator System",
    "version": "1.1.0",
    "author": "Your Organization",
    "description": "Generates various types of documents from Excel records"
  },
  "documents_types": [
    {
      "payment_advice": {
        "name": "Payment Advice",
        "schema": "payment_advice_schema.json",
        "template_data": [
          {
            "CONTACT_NUMBER_1": "123123123"
          },
          {
            "CONTACT_NUMBER_2": "123123123"
          }
        ]
      }
    }
  ],
  "html": {
    "images": {
      "UseBase64": true,
      "CopyToOutput": false
    }
  },
  "pdf": {
    "generator": "wkhtmltopdf",  // Options: wkhtmltopdf, weasyprint
    "page_size": "A4",
    "orientation": "portrait",
    "margin": "2cm",
    "font_size": "12pt",
    "text_color": "#333333",
    "background_color": "#ffffff",
    "wkhtmltopdf": "/usr/bin/wkhtmltopdf"  // Path to wkhtmltopdf executable
  },
  "database": {
    "driver": "sqlite",  // Only sqlite is currently supported
    "path": "data.db"
  },
  "storage": {
    "type": "disk",
    "path": "output"
  },
  "api": {
    "base_url": "http://localhost:8000",
    "auth_enabled": false,
    "auth_token": "dev-secret-key"
  },
  "logging": {
    "level": "DEBUG",
    "file": "logs/app.log",
    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
  }
}
```

### 3. Schema Files (schemas/*.json)

Schema files define document types, validation rules, field mappings, and output formats.

**Location**: `schemas/` directory
**Format**: JSON

**Example `schemas/payment_advice_schema.json`**:
```json
{
  "type": "payment_advice",
  "template": "payment_advice.html",
  "output_doc_name": "{datetime}_{SHAREHOLDER_ID_NUMBER}_payment_advice_{PAYMENT_REFERENCE}.{HTML|PDF}",
  "enums": {
    "COUNTRY_CODE": [
      "AF", "AX", "SB", "SO", "ZA", "GS", "SS", "ES"
    ]
  },
  "lists": {
    "COMPANY_NAME": [
      {
        "name": "Remgro Limited",
        "aliases": [
          "remgro",
          "remgro limited"
        ]
      },
      {
        "name": "Sasol Limited",
        "aliases": [
          "sasol",
          "sasol limited"
        ]
      }
    ],
    "BANK_NAME": [
      {
        "name": "First National Bank",
        "aliases": [
          "FNB",
          "first national bank"
        ]
      }
    ]
  },
  "schema": {
    "COMPANY_NAME": {
      "slug": ["COMPANY_NAME"],
      "validate_type": "LEV_DISTANCE",
      "list": "COMPANY_NAME",
      "distance": 80,
      "required": true
    },
    "SHAREHOLDER_ID_NUMBER": {
      "slug": ["SHAREHOLDER_ID_NUMBER"],
      "validate_type": "SA_ID_NUMBER",
      "required": true
    },
    "SHAREHOLDER_NUMBER": {
      "slug": ["SHAREHOLDER_NUMBER"],
      "validate_type": "REGEX",
      "regex": "^\\d{13}$",
      "required": true
    },
    "SHAREHOLDER_FULL_NAME": {
      "slug": ["SHAREHOLDER_FULL_NAME", "FULL_NAME"],
      "validate_type": "REGEX",
      "regex": "^([A-Z][a-z''\\-]+)(\\s+[A-Z][a-z''\\-]+)+$",
      "required": true
    },
    "ADDRESS_1": {
      "slug": ["ADDRESS_1", "ADDRESS1"],
      "validate_type": "REGEX",
      "regex": "^.{2,}$",
      "required": true
    },
    "ADDRESS_2": {
      "slug": ["ADDRESS_2", "ADDRESS2"],
      "validate_type": "REGEX",
      "regex": "^.{2,}$"
    },
    "ADDRESS_3": {
      "slug": ["ADDRESS_3", "ADDRESS3"],
      "validate_type": "REGEX",
      "regex": "^.{2,}$"
    },
    "ADDRESS_4": {
      "slug": ["ADDRESS_4", "ADDRESS4"],
      "validate_type": "REGEX",
      "regex": "^.{2,}$"
    },
    "ADDRESS_5": {
      "slug": ["ADDRESS_5", "ADDRESS5"],
      "validate_type": "REGEX",
      "regex": "^.{2,}$"
    },
    "POSTAL_CODE": {
      "slug": ["POSTAL_CODE"],
      "validate_type": "POSTAL_CODE"
    },
    "DOMICILE_CODE": {
      "slug": ["DOMICILE_CODE"],
      "validate_type": "ENUM",
      "enum": "COUNTRY_CODE",
      "required": true
    },
    "PAYMENT_DATE": {
      "slug": ["PAYMENT_DATE"],
      "validate_type": "UNIX_DATE",
      "required": true
    },
    "AMOUNT_PAID": {
      "slug": ["AMOUNT_PAID"],
      "validate_type": "DECIMAL_AMOUNT",
      "required": true
    },
    "BANK_NAME": {
      "slug": ["BANK_NAME"],
      "validate_type": "LEV_DISTANCE",
      "list": "BANK_NAME",
      "distance": 80,
      "required": true
    },
    "BANK_ACCOUNT_NUMBER": {
      "slug": ["BANK_ACCOUNT_NUMBER"],
      "validate_type": "BANK_ACCOUNT_NUMBER",
      "required": true
    },
    "PAYMENT_REFERENCE": {
      "slug": ["PAYMENT_REFERENCE"],
      "validate_type": "REGEX",
      "regex": "^\\d{13}$",
      "required": true
    }
  },
  "lookup_string": [
    "SHAREHOLDER_ID_NUMBER"
  ],
  "layout": {
    "margins": {
      "top": "0mm",
      "bottom": "0mm",
      "left": "0mm",
      "right": "0mm"
    }
  }
}
```

**Schema File Structure**:

1. **Basic Information**:
   - `type`: Document type identifier
   - `template`: HTML template filename in templates/html/
   - `output_doc_name`: Pattern for generated filenames

2. **Enums Section**:
   - Named lists of allowed values for field validation

3. **Lists Section**:
   - Named lists of complex items with aliases for fuzzy matching

4. **Schema Section**:
   - Field definitions with validation rules
   - Each field has:
     - `slug`: Alternative column names to match
     - `validate_type`: Validation method to use
     - `required`: Whether the field is required
     - Type-specific validation parameters

5. **Validation Types**:
   - `REGEX`: Regular expression pattern
   - `SA_ID_NUMBER`: South African ID number
   - `BANK_ACCOUNT_NUMBER`: Bank account number
   - `DECIMAL_AMOUNT`: Decimal currency amount
   - `UNIX_DATE`: Date in various formats
   - `POSTAL_CODE`: Postal/zip code
   - `ENUM`: Value from an enumerated list
   - `LEV_DISTANCE`: Fuzzy matching with Levenshtein distance

6. **Layout Section**:
   - PDF layout settings

### 4. Session Status File (status.json)

The status file tracks the current session and its state. This file is generated and maintained by the system.

**Location**: Root directory of the application
**Format**: JSON

**Example `status.json`**:
```json
{
  "last_updated": "2025-03-25T18:20:27+02:00",
  "current_state": {
    "hash": "ce65e00a455ca83cf53c6a687daa45ff52c0cd6732deae7c682beb3e5b60bbb3",
    "sqlite_db_file": "output/ce65e00a455ca83cf53c6a687daa45ff52c0cd6732deae7c682beb3e5b60bbb3/data.db",
    "imported_file": "test/data.csv",
    "document_type": "payment_advice",
    "output_folder": "output/ce65e00a455ca83cf53c6a687daa45ff52c0cd6732deae7c682beb3e5b60bbb3",
    "last_updated": "2025-03-25T18:20:20+02:00",
    "last_operation": "GENERATE_PDF"
  }
}
```

### 5. Field Mapping Files (output/\<hash>/mappings/\<hash>_mapping.json)

Mapping files link columns in imported data to fields in the schema. They are generated by the system but can be manually edited.

**Location**: `output/<session_hash>/mappings/<session_hash>_mapping.json`
**Format**: JSON

**Example mapping file**:
```json
{
  "COMPANY_NAME": "Company Name",
  "SHAREHOLDER_ID_NUMBER": "Shareholder ID Number",
  "SHAREHOLDER_NUMBER": "Shareholder Number",
  "SHAREHOLDER_FULL_NAME": "Shareholder Full Name",
  "ADDRESS_1": "Address 1",
  "ADDRESS_2": "Address 2",
  "ADDRESS_3": "Address 3",
  "ADDRESS_4": "Address 4",
  "ADDRESS_5": "Address 5",
  "POSTAL_CODE": "Postal Code",
  "DOMICILE_CODE": "Domicile Code",
  "PAYMENT_DATE": "Payment Date",
  "AMOUNT_PAID": "Amount Paid",
  "BANK_NAME": "Bank Name",
  "BANK_ACCOUNT_NUMBER": "Bank Account Number",
  "PAYMENT_REFERENCE": "Payment Reference"
}
```

## Starting the API Server

To start the API server:

```bash
# Linux
uvicorn api:app --host 0.0.0.0 --port 8000

# Windows
python -m uvicorn api:app --host 0.0.0.0 --port 8000
```

For development with auto-reload:

```bash
uvicorn api:app --reload
```

You can then access:
- API endpoints at `http://localhost:8000/`
- Interactive API documentation at `http://localhost:8000/docs`
- Alternative API documentation at `http://localhost:8000/redoc`

## Configuration Checklist

Before deploying the system, ensure you have:

1. **Basic Configuration**:
   - `.env` file with environment setting
   - Appropriate config file in `config/` directory

2. **Document Schemas**:
   - Schema file(s) in `schemas/` directory for each document type
   - Validation rules properly configured

3. **Templates**:
   - HTML templates in `templates/html/` directory
   - CSS stylesheets if needed

4. **PDF Generation**:
   - PDF generation tool installed (wkhtmltopdf or WeasyPrint)
   - Path to wkhtmltopdf executable correctly set in config

5. **API Configuration**:
   - API authentication settings if needed
   - Base URL and port settings

This comprehensive configuration allows the system to properly validate, transform, and generate documents according to your specific requirements.