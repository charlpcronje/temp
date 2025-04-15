# DocTypeGen - Intelligent Document Processing Platform

A modular, multi-interface system for ingesting, validating, mapping, and generating documents with comprehensive audit trails and reporting capabilities.

## 📋 Features

- Import CSV/Excel files into SQLite databases
- Automatically detect document type based on schema matching
- Validate data against predefined schemas
- Generate field-type mapping files
- Create HTML documents using Jinja2 templates
- Convert HTML to PDF using WeasyPrint or wkhtmltopdf
- Resolve lookups against external data sources
- Create entities based on document data
- Sync data to tenant databases
- Transfer files to S3 storage
- Generate comprehensive logs and reports
- Self-contained output folders for each processing session
- Dark mode support for all reports and dashboards
- Multiple interfaces: Web UI, CLI, REST API

## 🛠️ Technology Stack

- **Web UI**: React with Tailwind CSS
- **CLI Interface**: [Typer](https://typer.tiangolo.com)
- **REST API**: [FastAPI](https://fastapi.tiangolo.com)
- **Validation Models**: [Pydantic](https://docs.pydantic.dev)
- **Environment Management**: [python-dotenv](https://pypi.org/project/python-dotenv)
- **SQLite Interface**: `sqlite3` (standard lib)
- **HTML Template Rendering**: [Jinja2](https://jinja.palletsprojects.com)
- **PDF Generation**: [WeasyPrint](https://weasyprint.org/) or `wkhtmltopdf`
- **Data Parsing**: [pandas](https://pandas.pydata.org/)

## 🧩 Directory Structure

```
DocTypeGen/
├── cli.py                  # Typer CLI entry point
├── api.py                  # FastAPI REST entry point
├── commands.py             # Central registry of all command definitions
├── core/                   # All business logic modules
│   ├── importer.py         # Handles file imports
│   ├── validator.py        # Validates data against schemas
│   ├── mapper.py           # Manages field mappings
│   ├── html_generator.py   # Generates HTML documents
│   ├── pdf_generator.py    # Converts HTML to PDF
│   ├── logger.py           # HTML logging functions
│   └── session.py          # Handles status.json + config loader
├── public/                 # Web UI frontend
│   ├── src/                # React source code
│   ├── public/             # Static assets
│   └── package.json        # Frontend dependencies
├── templates/
│   ├── html/               # Jinja2 templates for document types
│   ├── logs/               # Templates for log HTML files
│   └── assets/             # CSS and other assets
├── schemas/                # JSON schema definitions
├── config/
│   ├── dev.json            # Development configuration
│   └── prod.json           # Production configuration
├── output/                 # Final output folders per session
│   └── {session_hash}/     # Session-specific outputs
│       ├── html/           # Generated HTML documents
│       ├── pdf/            # PDF versions
│       ├── www/            # Web dashboard
│       ├── logs/           # Log files
│       ├── mappings/       # Field mapping files
│       └── reports/        # Audit reports
├── .env                    # Contains ENV=dev or ENV=prod
└── status.json             # Tracks current session hash
```

## 🔧 Setup

### Prerequisites

- Python 3.10+
- Node.js 16+ (for Web UI)
- PDF generation tools (choose one):
  - `wkhtmltopdf` installed on your system
  - Python libraries for WeasyPrint

### Installation

1. Clone the repository:
   ```
   git clone https://github.com/yourusername/DocTypeGen.git
   cd DocTypeGen
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install backend dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Install frontend dependencies:
   ```
   cd public
   npm install
   cd ..
   ```

5. Configure environment:
   ```
   # Edit .env file
   echo "ENV=dev" > .env
   echo "debug=true" >> .env
   ```

## 📓 Usage

### Web UI

The web-based user interface provides a comprehensive dashboard for managing document processing:

```bash
# Start the API server
uvicorn api:app --reload

# Build and serve the frontend
cd public
npm run build
cd ..
```

Access the web UI at http://localhost:8000/app/

### CLI

The command-line interface provides access to all processing functionalities:

```bash
# Create a user
python cli.py user add username password --role admin

# Import a file
python cli.py import --file_path path/to/your/file.csv

# Validate the data
python cli.py validate

# Generate field mapping
python cli.py map

# Generate HTML files
python cli.py html

# Generate PDF files
python cli.py pdf

# Resolve lookups
python cli.py lookup

# Create entities
python cli.py entity

# Sync to tenant database
python cli.py sync

# Transfer to S3
python cli.py transfer

# View available commands
python cli.py list
```

### API

The REST API allows remote access to all features:

```bash
# Start the API server
uvicorn api:app --reload

# API will be available at http://localhost:8000
# SwaggerUI at http://localhost:8000/docs
```

API Endpoints:

- GET `/api/commands` - List available commands
- GET `/api/status` - Get current session status
- POST `/api/run/import` - Import a file by path
- POST `/api/run/import-upload` - Import an uploaded file
- POST `/api/run/validate` - Validate data
- POST `/api/run/map` - Generate field mapping
- POST `/api/run/html` - Generate HTML documents
- POST `/api/run/pdf` - Generate PDF documents
- POST `/api/run/lookup` - Resolve lookups
- POST `/api/sessions/{session_hash}/activate` - Activate a session
- GET `/api/files/{session_hash}/html/{filename}` - Serve HTML file
- GET `/api/files/{session_hash}/pdf/{filename}` - Serve PDF file

## 📂 Schemas

Schema files define document types, validation rules, and template information. Example:

```json
{
    "type": "payment_advice",
    "template": "payment_advice.html",
    "output_doc_name": "{datetime}_{SHAREHOLDER_ID_NUMBER}_payment_advice_{PAYMENT_REFERENCE}.{HTML|PDF}",
    "schema": {
        "COMPANY_NAME": {
            "slug": ["COMPANY_NAME"],
            "validate_type": "REGEX",
            "regex": "^.{2,}$",
            "required": true,
            "description": "Company name"
        },
        "SHAREHOLDER_NUMBER": {
            "slug": ["SHAREHOLDER_NUMBER"],
            "validate_type": "REGEX",
            "regex": "^\\d{13}$",
            "required": true,
            "description": "Shareholder identification number"
        }
    }
}
```

## 🖼️ Templates

Document templates use Jinja2 syntax and can access fields via the `record` object:

```html
<div id="address-section">
    <div id="name">{{ record.SHAREHOLDER_FULL_NAME }}</div>
    <div id="address1">{{ record.ADDRESS_1 }}</div>
</div>
```

## 📊 Output

Each processing session creates a self-contained output folder with:

- SQLite database with imported data
- Mapping files for field-column relationships
- HTML files generated from templates
- PDF files converted from HTML
- Comprehensive logs and reports
- Dashboard for browsing all outputs

## 🌓 Dark Mode

All reports and dashboards support dark mode, toggled by:

- User system preferences
- Toggle switch in the UI
- LocalStorage persistence

## 🧪 Development

To set up a development environment:

1. Install development dependencies:
   ```
   pip install -r requirements-dev.txt
   ```

2. Run the frontend in development mode:
   ```
   cd public
   npm run dev
   ```

3. Run the API server with auto-reload:
   ```
   uvicorn api:app --reload
   ```

## 📚 Documentation

For more detailed documentation, see the `docs/` directory:

- [Onboarding Guide](docs/onboarding.md)
- [Feature Details](docs/features.md)
- [Integration Guide](docs/integration_guide.md)
- [API Documentation](docs/api/README.md)
- [Validation System](docs/validation/README.md)
- [Lookup System](docs/lookup/README.md)