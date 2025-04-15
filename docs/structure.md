mytool/
├── cli.py                  # Typer CLI entry point
├── api.py                  # FastAPI REST entry point
├── commands.py             # Central registry of all command definitions
├── core/
│   ├── __init__.py
│   ├── importer.py
│   ├── validator.py
│   ├── mapper.py
│   ├── html_generator.py
│   ├── pdf_generator.py
│   ├── logger.py           # HTML logging functions
│   └── session.py          # Handles status.json + config loader
├── templates/
│   ├── html/               # Jinja2 templates for document types
│   │   └── payment_advice.html
│   ├── logs/               # Templates for log HTML files
│   │   ├── base.html
│   │   ├── dashboard.html
│   │   ├── import.html
│   │   ├── validate.html
│   │   ├── mapping.html
│   │   ├── generate_html.html
│   │   └── generate_pdf.html
│   └── assets/
│       ├── style.css       # Light mode CSS
│       └── dark-style.css  # Dark mode CSS
├── schemas/
│   └── payment_advice_schema.json
├── config/
│   ├── dev.json
│   └── prod.json
├── output/                 # Final output folders per session
│   └── <hash>/
│       ├── html/           # Generated HTML files
│       ├── pdf/            # Generated PDFs
│       ├── www/            # Static website view (logs + summary + styles)
│       ├── logs/           # Log files
│       ├── mappings/       # Editable field-type mapping files
│       └── data.db         # SQLite database
├── .env                    # Contains ENV=dev or ENV=prod
└── status.json             # Tracks current session hash

1. **Core Modules**:
   - `session.py`: Manages configuration, session state, and output directories
   - `importer.py`: Imports CSV/Excel files into SQLite
   - `validator.py`: Validates data against schemas and detects document types
   - `mapper.py`: Generates field mapping files
   - `html_generator.py`: Creates HTML files from templates and data
   - `pdf_generator.py`: Converts HTML to PDF files
   - `logger.py`: Generates HTML logs and reports

2. **Interfaces**:
   - `cli.py`: Command-line interface using Typer
   - `api.py`: REST API using FastAPI
   - `commands.py`: Central command registry for both interfaces

3. **Templates**:
   - HTML log templates for all processing steps
   - Example payment advice document template
   - Light and dark mode CSS files

4. **Documentation**:
   - Comprehensive README.md with setup and usage instructions
   - requirements.txt for dependency management

The system is designed to be modular, extensible, and user-friendly. It features:

- A clear separation of concerns between different modules
- Multiple interfaces (CLI and API) sharing the same core logic
- Comprehensive logging and reporting with a static HTML website output
- Dark mode support for better user experience
- Self-contained output directories for each processing session

Key features of the implementation include:

1. Automatic document type detection based on schema matching
2. Field-to-column mapping with validation
3. HTML generation with Jinja2 templates
4. PDF conversion using either WeasyPrint or wkhtmltopdf
5. Detailed logs and validation reports
6. A dashboard for browsing outputs and logs
7. Configuration management with environment variables

Users can process documents through a simple workflow:
1. Import data (`import`)
2. Validate and detect document type (`validate`)
3. Generate field mapping (`map`)
4. Create HTML documents (`html`)
5. Convert to PDF (`pdf`)

Alternatively, users can run all steps in sequence with a single command (`all`).

This implementation meets all the requirements specified in the original task and provides a solid foundation for future extensions.