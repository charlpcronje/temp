✅ **Static Document Processing Engine**

---

### 🧠 **Purpose**

You are building a **modular Python system** that ingests Excel/CSV files, detects document types, generates populated HTML/PDF documents, and produces a **fully browsable static HTML website** containing validation reports, logs, and final outputs—**all bundled in a single, portable, self-contained output folder** per session.

---

### ⚙️ **Technology Stack**

| Feature                      | Tech                         |
|-----------------------------|------------------------------|
| CLI Interface               | [`Typer`](https://typer.tiangolo.com)                     |
| REST API                    | [`FastAPI`](https://fastapi.tiangolo.com)                  |
| Shared Command Layer        | Custom `commands.py` registry           |
| Validation Models           | [`Pydantic`](https://docs.pydantic.dev)                   |
| Environment Management      | [`python-dotenv`](https://pypi.org/project/python-dotenv) |
| Config Files                | JSON in `config/{ENV}.json`             |
| SQLite Interface            | `sqlite3` (standard lib) or `SQLAlchemy` if needed        |
| HTML Template Rendering     | `Jinja2`                                |
| PDF Generation              | [`WeasyPrint`](https://weasyprint.org/) or `wkhtmltopdf`  |
| Static HTML Logging         | Custom HTML generator with templates    |
| File/Folder Hashing         | `hashlib.sha256`                       |
| File Parsing                | [`pandas`](https://pandas.pydata.org/) for CSV/XLSX       |
| Templating for Logs         | Optional: `Jinja2` + shared styles      |
| StyleSheet for WebView      | Copied from `templates/style.css`       |

---

### 🧱 **Directory Structure**

```
mytool/
├── cli.py                  # Typer CLI entry point
├── api.py                  # FastAPI REST entry point
├── commands.py             # Central registry of all command definitions
├── core/                   # All business logic modules
│   ├── importer.py
│   ├── validator.py
│   ├── mapper.py
│   ├── html_generator.py
│   ├── pdf_generator.py
│   ├── logger.py           # HTML logging functions
│   └── session.py          # Handles status.json + config loader
├── templates/
│   ├── html/               # Jinja2 templates for document types
│   └── style.css           # Global stylesheet copied to each output
├── schemas/                # JSON schema definitions (e.g., payment_advice.json)
├── config/
│   ├── dev.json
│   └── prod.json
├── output/                 # Final output folders per session
│   └── <hash>/
│       ├── html/           # Generated HTML files
│       ├── pdf/            # Generated PDFs
│       ├── www/            # Static website view (logs + summary + style.css)
│       ├── logs/           # Log files
│       ├── mappings/       # Editable field-type mapping files
├── .env                    # Contains ENV=dev or ENV=prod
└── status.json             # Tracks current session hash
```

---

### 📋 **Phases and Logic**

#### 🔹 **Step 1: Import File**
- Accept `.csv` or `.xlsx`
- Compute SHA256 hash of contents
- Store data in `sqlite` using the hash as the table name
- Save all columns as text (raw preservation)
- Update or create `status.json` with current session hash
- Generate `import.html` log in `output/<hash>/www/`

#### 🔹 **Step 2: Validate Data**
- Load schema(s) from `schemas/`
- Match column contents to field types (e.g., `SA_ID_NUMBER`, `DATE`)
- Determine best-fit document type by match count
- Generate:
  - `validate.html` (high-level)
  - `validate_row_0001.html`, etc. (detailed per-row)
- Log reason for selected document type

#### 🔹 **Step 3: Generate Mapping File**
- Generate `output/<hash>/mappings/{hash}_mapping.json`:
  ```json
  {
    "first_name": "FULL_NAME",
    "postal": "POSTAL_CODE"
  }
  ```
- Allows user to override AI-inferred types
- `mapper.py` must read this back in next step
- Log output to `output/<hash>/mapping.html`

#### 🔹 **Step 4: Generate HTML Documents**
- Load correct template based on detected document type
- Substitute placeholders like `{{FULL_NAME}}` using actual column names from mapping
- Save one `.html` file per row to `output/<hash>/html/`
- Generate `generate_html.html` + `html_row_0001.html`, etc. logs

#### 🔹 **Step 5: Generate PDFs**
- Use `wkhtmltopdf`, or similar
- One `.pdf` per `.html`
- Save to `output/<hash>/pdf/`
- Log to `generate_pdf.html`

#### 🔹 **Final Summary Report**
- Create `output/<hash>/www/index.html`
- Links to:
  - All phase logs
  - All per-row reports
  - All generated PDFs and HTMLs
- Copy `templates/style.css` into `output/<hash>/www/` for consistent design

---

### 🔐 **Session Persistence**
- `status.json` must persist current session hash
- Allows app to resume after interruption or manual restart
- App reads from it by default unless a new import is triggered

---

### 🔧 **Environment Config**
- `.env` contains: `ENV=dev`
- Loads config from `config/{ENV}.json`
- Contains:
  - Output path
  - SQLite DB path
  - Template paths
  - Storage settings

---

### 🧩 **commands.py (Shared Command Registry)**

```python
# commands.py

from core.importer import import_file
from core.validator import validate_data
from core.mapper import generate_mapping_file
from core.html_generator import generate_html_files
from core.pdf_generator import generate_pdfs

COMMANDS = {
    "import": {
        "func": import_file,
        "args": ["file_path"],
        "description": "Import a CSV or Excel file into SQLite."
    },
    "validate": {
        "func": validate_data,
        "args": [],
        "description": "Validate the active session and detect document type."
    },
    "map": {
        "func": generate_mapping_file,
        "args": [],
        "description": "Generate editable field-type mapping for this session."
    },
    "html": {
        "func": generate_html_files,
        "args": [],
        "description": "Generate HTML files from mapped, validated data."
    },
    "pdf": {
        "func": generate_pdfs,
        "args": [],
        "description": "Generate PDFs from HTML templates."
    }
}
```

---

### ✅ **Execution Interfaces**

#### 🔸 **CLI (Typer)**
- `cli.py` auto-loads commands from `commands.py`
- Run: `python cli.py import somefile.csv`

#### 🔸 **API (FastAPI)**
- `api.py` exposes `/run/{command}` endpoints
- Accepts arguments in JSON body
- Runs the same logic as CLI

#### 🔸 **TUI (Textual)**
**⏳ Not implemented yet — will be added in Phase 2**
- Will use `commands.py` to render menus, prompts, and logs
- No additional planning required now

---

### 🎯 **Final Behavior Summary**

- App is modular, layered, and interface-agnostic
- Each session is **completely self-contained in `output/<hash>/`**
- Logs, HTML, PDFs, mapping, and config are all local to that hash
- Output folder can be zipped and uploaded to S3 as-is
- The `output/<hash>/www/` folder is a fully browsable **static website with logs and reports**

---

Let me know if you want me to:
- Write a starter `logger.py`
- Scaffold the CLI and API files with dynamic command loading
- Include base templates for `style.css`, `base.html`, and `logs_{document_type}_validation.html` ...
- I did supply templates for all the html reporting but I'd like dark mode css as well and the css should not be built into the html and I want the app to build out a dashboard for the user to view the logs and reports, so we also need a template for that