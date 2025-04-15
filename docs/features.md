# Digital Cabinet | Document Generation & Audit

## I. Core Backend Functionality (Supports all interfaces)

### Session Management (`core/session.py`)
- Manages application state via `status.json`.
- Loads environment-specific configurations (`config/*.json`).
- Creates and manages session-specific output directories (`output/{hash}/`).
- Computes file hashes (SHA256) to identify sessions.
- Copies static assets (CSS) to session directories.

### Data Import (`core/importer.py`)
- Imports data from CSV and Excel (.xlsx, .xls) files.
- Detects file encoding and converts to UTF-8 with LF line endings if necessary.
- Stores imported data in a session-specific SQLite database (`output/{hash}/data.db`).
- Creates `import_meta` table to store import metadata.
- Handles large CSV files using chunking.
- Sanitizes column names for database compatibility.
- Provides functions to retrieve table data and column info.

### Data Validation (`core/validator.py`)
- Loads document schemas from the `schemas/` directory.
- Compares imported data against schemas to detect the best-matching document type.
- Performs field-level validation based on schema rules (REGEX, SA_ID_NUMBER, BANK_ACCOUNT_NUMBER, DECIMAL_AMOUNT, UNIX_DATE, ENUM, LEV_DISTANCE, etc.).
- Calculates validation success rates and identifies invalid rows/fields.
- Respects existing manual mappings if found.

### Field Mapping (`core/mapper.py`)
- Generates an initial field-to-column mapping file (`mappings/{hash}_mapping.json`) based on validation results.
- Loads existing mapping files.
- Allows updating and deleting mapping files.
- Checks for missing required field mappings.

### HTML Generation (`core/html_generator.py`)
- Generates HTML documents based on Jinja2 templates (`templates/html/`).
- Uses the field mapping to populate templates with data from the session database.
- Creates filenames based on patterns defined in the schema.
- Stores metadata about generated HTML documents in the session database (`generated_{table_hash}`).

### PDF Generation (`core/pdf_generator.py`)
- Converts generated HTML files to PDF using `wkhtmltopdf` or `weasyprint`.
- Supports parallel processing for `wkhtmltopdf`.
- Stores metadata about generated PDF documents in the session database.

### Logging (`core/logger.py`):
- Generates detailed HTML log files for each processing step (import, validate, map, html, pdf).
- Creates execution summaries and a main dashboard (`index.html`) within the session's `www/` directory.
- Uses Jinja2 templates (`templates/logs/`) for log formatting.
- Supports dark/light mode styling via separate CSS files (`templates/assets/`).

### Authentication (`core/auth/`)
- User database management (SQLite via `auth_db_manager.py`).
- Secure password hashing (PBKDF2-SHA256).
- JWT token generation and validation (`jwt_auth.py`).
- Role-based access control (user/admin).

### Lookup Resolution (`core/lookup_resolver.py`)
- Matches document records against external data sources based on tenant mappings in config.
- Supports `column_to_column` and `type_to_column` mapping types.
- Connects to local SQLite and (simulated) MySQL.
- Logs lookup attempts and exceptions to session DB tables (`tenant_lookup_*`).
- Updates `generated_*` table with lookup results.
- Provides functionality to resolve exceptions manually.

### Reporting (`core/reporter.py`, `core/report_db.py`)
- Creates data snapshots (`lookups_snapshot_{table_hash}`) for reproducible reports.
- Generates multiple report types (summary, mapping, verify, exceptions) in HTML and PDF.
- Stores report metadata in session DB tables (`report_runs`, `lookups_snapshot_reports`)
- Calculates table hashes to check report freshness.
- Supports regenerating reports (`rerun_report`)
- Provides report listing functionality (`list_reports`)

### Command Orchestration (`commands.py`)
- Central registry (`COMMANDS`) mapping command names to core functions, arguments, and descriptions.
- `run_command` function executes commands, ensuring session validity where needed.
- `list_commands` provides metadata about available commands.

### **II. CLI Features (`cli.py`)**

### Core Commands:**
- `import <file_path> [options]`: Import data file.
- `validate`: Validate data and detect document type.
- `map`: Generate/view field mapping.
- `html`: Generate HTML documents.
- `pdf`: Generate PDF documents.
- `all <file_path>`: Run the entire workflow (import to pdf).
- `list`: List all available commands.
- `resolve_lookups [--session HASH]`: Run lookup resolution.
- `report_generate`: Generate all reports for the current session.
- `report_rerun <report_id>`: Regenerate a specific report batch.
- `report_list`: List all generated report runs.

### User Management (`user` subcommand):
- `user add <username> <password> [--role ROLE]`: Add a new user.
- `user list`: List all users.
- `user password <username> <new_password>`: Change a user's password.
- `user role <username> <new_role>`: Change a user's role.
- `user status <username> <is_active>`: Activate or deactivate a user.
- `user delete <username> [--force]`: Delete a user.
- **Output:** Uses Rich library for formatted tables and status messages. Provides symbols (`core/symbols.py`).
- **Options:** `--verbose` and `--quiet` flags to control output level.

###  III. API Features (`api.py`)

### **Server:** 
FastAPI application run with Uvicorn.

### **Static File Serving:**
- Serves the built React dashboard (`public/dist`) from the root (`/`).
- Serves session-specific outputs (HTML, PDF, logs) under `/static/{hash}/...`.
- Serves general logs from `output/` under `/logs`.
- Supports SPA routing by serving `index.html` for unhandled paths.

### **Endpoints:**
- `/api/status`: Get current session status.
- `/api/commands`: List available commands.
- `/api/run/import`: Import file via server path (form data).
- `/api/run/import-upload`: Import file via direct upload (multipart/form-data).
- `/api/run/{command}`: Generic endpoint to run any command (`validate`, `map`, `html`, `pdf`, `all`, etc.) with JSON body for args.
- `/api/auth/login`: Authenticate username/password, returns JWT token.
- `/api/auth/token`: OAuth2 compatible login for Swagger UI.
- `/api/auth/me`: Get authenticated user's details (requires token).
- `/api/auth/verify`: Verify token validity.
- `/api/auth/users`: List users (admin only, requires token).

- `PUT /api/auth/users`: Update user (admin only, requires token).
- `/api/logs`: List all session log directories.
- `/api/logs/{hash}`: Get details for a specific session log directory.

- `POST /api/logs/{hash}/rename`: Rename a session log.
- `/api/helper/{issue_id}`: Get troubleshooting help text.
- `/api/helper/`: List available help topics.
- `/api/report/generate`: Generate reports for the current session.
- `/api/report/rerun`: Rerun a specific report batch (needs `report_id` in body).
- `/api/report/list`: List all report runs.
- `/api/report/{report_id}/html/{filename}`: Serve specific HTML report file.
- `/api/report/{report_id}/pdf/{filename}`: Serve specific PDF report file.

>> **Authentication:** Optional API key (`X-API-Key` header) or JWT Bearer token (`Authorization` header) based on configuration.

### IV. TUI Features (`tui.py`)

- **Interface:** Full-screen terminal UI built with Textual.
- **Layout:**
    - Left Panel: List of available commands (dynamically loaded from `commands.py`).
    - Right Panel: Details of selected command (description, args), current session info.
    - Bottom Panel: Live log output.

- **Functionality:**
    - Navigate commands using keyboard/mouse.
    - Run commands by pressing Enter.
    - Prompts for required command arguments using a modal dialog.
    - Displays command execution progress and results in the log panel.
    - Provides access to a dedicated "Reports" screen.

- **Reports Screen:**
    - Lists generated reports with status (Valid/Stale).
    - Allows generating new reports.
    - Allows rerunning selected reports.
    - Provides options to view report HTML/PDF (opens in default browser).
    - **Bindings:** Keyboard shortcuts for quitting, clearing logs, accessing reports.

### V. Web UI (Dashboard) Features (`public/src/`)

- **Framework:** React with TypeScript, Vite bundler.
- **UI Library:** ShadCN UI components.
- **Routing:** React Router (`/app/*` routes).
- **State Management:** React Context API (Auth, Theme), Tanstack Query for API data fetching.
- **Authentication:**
    - Login page (`/login`).
    - Protected routes requiring authentication.
    - Admin-only routes (e.g., User Management).
    - Supports JWT or API Key mode based on config.
- **Layout:** Responsive Dashboard layout with Header and Sidebar.
- **Core Pages:**

**Dashboard (`/app/dashboard`)** Overview cards, recent sessions, active session indicator, admin controls link.
    
**Workflow (`/app/workflow`)** Multi-step process guide:
    - Upload Step (`/app/workflow/upload`): Drag & drop file upload with validation.
    - Validate Step: Displays validation results, success rate, field match details, row errors. Allows editing mappings.
    - Map Step: Displays/edits column-to-type mappings. Allows saving changes and re-validating.
    - HTML Generation Step: Shows progress and results of HTML generation, previews files.
    - PDF Generation Step: Shows progress and results of PDF generation, previews/downloads files.
    - Lookup Resolution Step: Shows lookup status, allows triggering resolution, displays results/exceptions in tabs, links to exception resolver.
    - Entity Creation Step: Lists entities marked for creation, allows creating them.
    - Sync Step: Interface to trigger sync to tenant DB.
    - Storage Step: Interface to trigger transfer to S3.

### **Sessions (`/app/sessions`)** Lists all processing sessions, allows searching, renaming, opening in workflow, viewing logs.
- **Logs (`/app/logs`, `/app/logs/{id}`):** Lists log directories (same as sessions), displays detailed log - info with file previews (HTML, PDF, Logs).
- **User Management (`/app/users` - Admin Only):** CRUD operations for users (list, add, edit, delete).
- **Settings (`/app/settings`):** User profile settings, theme toggle, password change, notification preferences (placeholders for now).
- **Components:** Reusable UI elements for tables, forms, dialogs, status badges, spinners, etc. Includes specific components for lookup resolution (`ExceptionsTable`, `ForCreationTable`, `LookupExceptionResolver`).
- **API Integration:** Uses `axios` client (`api/client.ts`) with interceptors for auth; dedicated service functions (`api/services.ts`) for API calls.
- **Theme:** Dark/Light mode toggle using ThemeContext and localStorage.




## Digital Cabinet: Document Generator and Audits

### I. Core Backend Functionality (Supports all interfaces)

- **Session Management (`core/session.py`)**
    - Manages application state via `status.json`.
    - Loads environment-specific configurations (`config/*.json`).
    - Creates and manages session-specific output directories (`output/{hash}/`).
    - Computes file hashes (SHA256) to identify sessions.
    - Copies static assets (CSS) to session directories.

- **Data Import (`core/importer.py`)**
    - Imports data from CSV and Excel (.xlsx, .xls) files.
    - Detects file encoding and converts to UTF-8 with LF line endings if necessary.
    - Stores imported data in a session-specific SQLite database (`output/{hash}/data.db`).
    - Creates `import_meta` table to store import metadata.
    - Handles large CSV files using chunking.
    - Sanitizes column names for database compatibility.
    - Provides functions to retrieve table data and column info.

- **Data Validation (`core/validator.py`)**
    - Loads document schemas from the `schemas/` directory.
    - Compares imported data against schemas to detect the best-matching document type.
    - Performs field-level validation based on schema rules (REGEX, SA_ID_NUMBER, BANK_ACCOUNT_NUMBER, DECIMAL_AMOUNT, UNIX_DATE, ENUM, LEV_DISTANCE, etc.).
    - Calculates validation success rates and identifies invalid rows/fields.
    - Respects existing manual mappings if found.

- **Field Mapping (`core/mapper.py`)**
    - Generates an initial field-to-column mapping file (`mappings/{hash}_mapping.json`) based on validation results.
    - Loads existing mapping files.
    - Allows updating and deleting mapping files.
    - Checks for missing required field mappings.

- **HTML Generation (`core/html_generator.py`)**
    - Generates HTML documents based on Jinja2 templates (`templates/html/`).
    - Uses the field mapping to populate templates with data from the session database.
    - Creates filenames based on patterns defined in the schema.
    - Stores metadata about generated HTML documents in the session database (`generated_{table_hash}`).

- **PDF Generation (`core/pdf_generator.py`)**
    - Converts generated HTML files to PDF using `wkhtmltopdf` or `weasyprint`.
    - Supports parallel processing for `wkhtmltopdf`.
    - Stores metadata about generated PDF documents in the session database.

- **Logging (`core/logger.py`)**
    - Generates detailed HTML log files for each processing step (import, validate, map, html, pdf).
    - Creates execution summaries and a main dashboard (`index.html`) within the session's `www/` directory.
    - Uses Jinja2 templates (`templates/logs/`) for log formatting.
    - Supports dark/light mode styling via separate CSS files (`templates/assets/`).

- **Authentication (`core/auth/`)**
    - User database management (SQLite via `auth_db_manager.py`)
    - Secure password hashing (PBKDF2-SHA256)
    - JWT token generation and validation (`jwt_auth.py`)
    - Role-based access control (user/admin)

- **Lookup Resolution (`core/lookup_resolver.py`)**
    - Matches document records against external data sources based on tenant mappings in config.
    - Supports `column_to_column` and `type_to_column` mapping types.
    - Connects to local SQLite and (simulated) MySQL.
    - Logs lookup attempts and exceptions to session DB tables (`tenant_lookup_*`).
    - Updates `generated_*` table with lookup results.
    - Provides functionality to resolve exceptions manually.

- **Reporting (`core/reporter.py`, `core/report_db.py`)**
    - Creates data snapshots (`lookups_snapshot_{table_hash}`) for reproducible reports.
    - Generates multiple report types (summary, mapping, verify, exceptions) in HTML and PDF.
    - Stores report metadata in session DB tables (`report_runs`, `lookups_snapshot_reports`).
    - Calculates table hashes to check report freshness.
    - Supports regenerating reports (`rerun_report`)
    - Provides report listing functionality (`list_reports`)
    - **Command Orchestration (`commands.py`):**
    - Central registry (`COMMANDS`) mapping command names to core functions, arguments, and descriptions.
    - `run_command` function executes commands, ensuring session validity where needed.
    - `list_commands` provides metadata about available commands.

### II. CLI Features (`cli.py`)

- **Core Commands:**
    - `import <file_path> [options]`: Import data file.
    - `validate`: Validate data and detect document type.
    - `map`: Generate/view field mapping.
    - `html`: Generate HTML documents.
    - `pdf`: Generate PDF documents.
    - `all <file_path>`: Run the entire workflow (import to pdf).
    - `list`: List all available commands.
    - `resolve_lookups [--session HASH]`: Run lookup resolution.
    - `report_generate`: Generate all reports for the current session.
    - `report_rerun <report_id>`: Regenerate a specific report batch.
    - `report_list`: List all generated report runs.

- **User Management (`user` subcommand):**
    - `user add <username> <password> [--role ROLE]`: Add a new user.
    - `user list`: List all users.
    - `user password <username> <new_password>`: Change a user's password.
    - `user role <username> <new_role>`: Change a user's role.
    - `user status <username> <is_active>`: Activate or deactivate a user.
    - `user delete <username> [--force]`: Delete a user.
- **Output:** Uses Rich library for formatted tables and status messages. Provides symbols (`core/symbols.py`).**
- **Options:** `--verbose` and `--quiet` flags to control output level.**

### III. API Features (`api.py`)

- **Server:** FastAPI application run with Uvicorn.**
- **Static File Serving:**
    - Serves the built React dashboard (`public/dist`) from the root (`/`).
    - Serves session-specific outputs (HTML, PDF, logs) under `/static/{hash}/...`.
    - Serves general logs from `output/` under `/logs`.
    - Supports SPA routing by serving `index.html` for unhandled paths.

- **Endpoints:**
    - `/api/status`: Get current session status.
    - `/api/commands`: List available commands.
    - `/api/run/import`: Import file via server path (form data).
    - `/api/run/import-upload`: Import file via direct upload (multipart/form-data).
    - `/api/run/{command}`: Generic endpoint to run any command (`validate`, `map`, `html`, `pdf`, `all`, etc.) with JSON body for args.
    - `/api/auth/login`: Authenticate username/password, returns JWT token.
    - `/api/auth/token`: OAuth2 compatible login for Swagger UI.
    - `/api/auth/me`: Get authenticated user's details (requires token).
    - `/api/auth/verify`: Verify token validity.
    - `/api/auth/users`: List users (admin only, requires token).
    - `PUT /api/auth/users`: Update user (admin only, requires token).
    - `/api/logs`: List all session log directories.
    - `/api/logs/{hash}`: Get details for a specific session log directory.
    - `POST /api/logs/{hash}/rename`: Rename a session log.
    - `/api/helper/{issue_id}`: Get troubleshooting help text.
    - `/api/helper/`: List available help topics.
    - `/api/report/generate`: Generate reports for the current session.
    - `/api/report/rerun`: Rerun a specific report batch (needs `report_id` in body).
    - `/api/report/list`: List all report runs.
    - `/api/report/{report_id}/html/{filename}`: Serve specific HTML report file.
    - `/api/report/{report_id}/pdf/{filename}`: Serve specific PDF report file.

>> **Authentication:** Optional API key (`X-API-Key` header) or JWT Bearer token (`Authorization` header) based on configuration.

### IV. TUI Features (`tui.py`)

- **Interface:** Full-screen terminal UI built with Textual.**
- **Layout:****
    - Left Panel: List of available commands (dynamically loaded from `commands.py`).
    - Right Panel: Details of selected command (description, args), current session info.
    - Bottom Panel: Live log output.

- **Functionality:**
    - Navigate commands using keyboard/mouse.
    - Run commands by pressing Enter.
    - Prompts for required command arguments using a modal dialog.
    - Displays command execution progress and results in the log panel.
    - Provides access to a dedicated "Reports" screen.
    - **Reports Screen:**
    - Lists generated reports with status (Valid/Stale).
    - Allows generating new reports.
    - Allows rerunning selected reports.
    - Provides options to view report HTML/PDF (opens in default browser).
- **Bindings:** Keyboard shortcuts for quitting, clearing logs, accessing reports.

### V. Web UI (Dashboard) Features (`public/src/`)

- **Framework:** React with TypeScript, Vite bundler.
- **UI Library:** ShadCN UI components
- **Routing:** React Router (`/app/*` routes)
- **State Management:** React Context API (Auth, Theme), Tanstack Query for API data fetching.
- **Authentication:**
    - Login page (`/login`).
    - Protected routes requiring authentication.
    - Admin-only routes (e.g., User Management)
    - Supports JWT or API Key mode based on config.
- **Layout:** Responsive Dashboard layout with Header and Sidebar.
- **Core Pages:**
- **Dashboard (`/app/dashboard`):** Overview cards, recent sessions, active session indicator, admin controls link.
- **Workflow (`/app/workflow`):** Multi-step process guide:
    - Upload Step (`/app/workflow/upload`): Drag & drop file upload with validation.
    - Validate Step: Displays validation results, success rate, field match details, row errors. Allows editing mappings.
    - Map Step: Displays/edits column-to-type mappings. Allows saving changes and re-validating.
    - HTML Generation Step: Shows progress and results of HTML generation, previews files.
    - PDF Generation Step: Shows progress and results of PDF generation, previews/downloads files.
    - Lookup Resolution Step: Shows lookup status, allows triggering resolution, displays results/exceptions in tabs, links to exception resolver.
    - Entity Creation Step: Lists entities marked for creation, allows creating them.
    - Sync Step: Interface to trigger sync to tenant DB.
    - Storage Step: Interface to trigger transfer to S3.
- **Sessions (`/app/sessions`):** Lists all processing sessions, allows searching, renaming, opening in workflow, viewing logs.
- **Logs (`/app/logs`, `/app/logs/{id}`):** Lists log directories (same as sessions), displays detailed log info with file previews (HTML, PDF, Logs).
- **User Management (`/app/users` - Admin Only):** CRUD operations for users (list, add, edit, delete).
- **Settings (`/app/settings`):** User profile settings, theme toggle, password change, notification preferences (placeholders for now).
- **Components:** Reusable UI elements for tables, forms, dialogs, status badges, spinners, etc. Includes specific components for lookup resolution (`ExceptionsTable`, `ForCreationTable`, `LookupExceptionResolver`).
- **API Integration:** Uses `axios` client (`api/client.ts`) with interceptors for auth; dedicated service functions (`api/services.ts`) for API calls.
- **Theme:** Dark/Light mode toggle using ThemeContext and localStorage.


## Where 
### **1. Modularity and Separation of Concerns:**
- The core logic (import, validate, map, generate, log, session, auth, lookup, report) is separated into distinct modules within the `core/` directory. This makes the system easier to understand, maintain, test, and extend.
- Interfaces (CLI, API, TUI, Web) are kept separate from the core logic, allowing new interfaces to be added or existing ones modified without disrupting the fundamental processing pipeline.

### **2. Multiple Interfaces for Different Needs:**
- **CLI (`cli.py`):** Good for scripting, automation, and power users comfortable with the command line. Uses Rich for better output.
- **API (`api.py`):** Enables integration with other systems, programmatic control, and powers the web dashboard. Built with FastAPI, providing automatic interactive documentation (`/docs`).
- **TUI (`tui.py`):** Offers an interactive, terminal-based experience for users who prefer not to leave the terminal but want more guidance than the raw CLI. Uses Textual for a modern TUI.
- **Web UI (Dashboard) (`public/`):** Provides a rich, graphical interface (React + ShadCN) for less technical users, offering visual feedback, step-by-step guidance, and easier management of sessions and users.

### 3. Centralized Command Logic (`commands.py`)
- Defines all core operations in one place, mapping command names to functions, arguments, and descriptions.
- Ensures consistency across all interfaces (CLI, API, TUI, Web) as they all call the same underlying functions via `run_command`.

### 4. Configuration-Driven:
- Uses environment variables (`.env`) and JSON configuration files (`config/`) to manage settings for different environments (dev, prod).
- Document types, validation rules, and template details are defined externally in schema files (`schemas/*.json`), making the system adaptable to new document types without code changes.
- Tenant-specific configurations (database connections, mappings) are supported.

### 5. Robust Session Management (`core/session.py`)
- Each processing run is tied to a unique session hash derived from the input file.
- Maintains state in `status.json`, allowing processes to be potentially resumed or understood later.
- Creates self-contained output directories (`output/{hash}/`) for each session, organizing all related artifacts (data, logs, HTML, PDF, mappings, reports).

### 6. Comprehensive Logging and Reporting:**
- Generates detailed HTML logs (`core/logger.py`) for each step, providing visibility into the process.
- Produces a static, browsable website (`output/{hash}/www/`) for each session, consolidating logs and outputs.
- Includes a dedicated Reporting System (`core/reporter.py`, `core/report_db.py`) that creates data snapshots for auditability and generates multiple report types (summary, mapping, verification, exceptions) in both HTML and PDF.

### 7. Data Integrity and Validation:
- Performs schema-based validation (`core/validator.py`) early in the process.
- Includes specific validation logic for types like SA ID numbers, bank accounts, dates, etc.
- Uses Levenshtein distance for fuzzy matching where appropriate.
- Handles file encoding issues during import.

### 8. User Authentication and Authorization:
- Provides a proper user management system (`core/auth/`) with secure password hashing and role-based access (admin/user).
- Supports both JWT and simple API Key authentication for the API.

### 9. Lookup and Data Enrichment (`core/lookup_resolver.py`)
- Includes a dedicated phase for resolving lookups against external data sources (defined in tenant config).
- Handles exceptions gracefully and provides mechanisms for manual resolution.

### 10. Modern Technology Choices:*
- Utilizes well-regarded, modern libraries like: 
- FastAPI
- Typer
- Textual
- React
- ShadCN
- Pydantic,
- Pandas
- Jinja2s