Brilliant — let’s lock in this phase formally with a **complete updated spec**, followed by a **modular, role-specific task breakdown** that aligns **CLI, API, TUI, and Dashboard** via a shared backend architecture.

You’ll have:

- ✅ Updated unified spec
- ✅ General backend task list (core logic + shared infra)
- ✅ Role-specific task lists for CLI, API, TUI, Dashboard
- ✅ Aligned interface expectations

---

## ✅ Updated Spec: Snapshot-Aware Report Generator

### 🎯 Objective
Build a unified reporting system that, for every validated session:
- Freezes a snapshot of the data table
- Generates all relevant HTML reports
- Converts them to PDFs
- Stores and traces every report in a report metadata table
- Serves reports from all interfaces (CLI, API, TUI, Dashboard)
- Produces a static site + JSON metadata
- Ensures all reports are reproducible and auditable

---

## 📂 Final Output Structure

```
output/
└── {session_hash}/
    ├── reports/
    │   └── hash{generated_{table_hash}}/
    │       ├── summary.html
    │       ├── summary.pdf
    │       ├── verify.html
    │       ├── verify.pdf
    │       ├── mapping.html
    │       ├── mapping.pdf
    │       ├── ...
    │       ├── meta.json
    │       └── style.css
    ├── html/
    ├── pdf/
    └── www/
        └── index.html (links to reports/)
```

---

## 🧱 Core System Components

### 🔁 1. **Snapshot Table**
- Duplicates the active session SQLite table
- Named `lookups_snapshot_{table_hash}`

### 📊 2. **Report Metadata Table**
Table: `lookups_snapshot_reports`

| Column        | Type     | Description |
|---------------|----------|-------------|
| `id`          | INT      | Primary key |
| `snapshot_table` | TEXT  | Name of snapshot table |
| `report_name` | TEXT     | Display/report name |
| `report_type` | TEXT     | e.g., `summary`, `validation`, `exceptions` |
| `template_used` | TEXT   | Jinja2 or HTML template name |
| `path`        | TEXT     | Folder path to report |
| `html_file`   | TEXT     | HTML filename |
| `pdf_file`    | TEXT     | PDF filename |
| `source_hash` | TEXT     | SHA256 of original file |
| `created_at`  | DATETIME | Timestamp |

---

### 📦 3. **meta.json**
Describes the session, document type, output files, generation history.

---

## 🧠 General Tasks (Backend / Shared Infrastructure)

| Task | Description |
|------|-------------|
| `generate_snapshot_table()` | Copies session table into `lookups_snapshot_{table_hash}` |
| `render_report(template, data)` | Renders report as HTML |
| `convert_html_to_pdf(html_path)` | Uses PDF engine to convert HTML to PDF |
| `record_report_metadata()` | Inserts a row into `lookups_snapshot_reports` |
| `generate_meta_json()` | Creates `meta.json` for static session summary |
| `copy_style()` | Copies `style.css` to output folder |
| `reporter.py` | Core file containing `generate_all_reports()` and supporting utilities |
| `register_commands()` | Add `report_generate` to `commands.py` |
| `create_reports_folder()` | Ensures structured folders are created properly |
| `link_in_dashboard()` | Dashboard links dynamically to reports based on metadata table |

---

## 🧪 Reports to Generate

| Report Name | Template | Report Type |
|-------------|----------|-------------|
| `summary.html` | `summary.jinja2` | `summary` |
| `mapping.html` | `mapping.jinja2` | `mapping` |
| `verify.html` | `verify.jinja2` | `user_match` |
| `exceptions.html` | `exceptions.jinja2` | `exceptions` |

Each report has:
- HTML version
- PDF version
- Record in metadata DB

---

## 📋 CLI Task List

| Task | Description |
|------|-------------|
| `report_generate` command | Add to CLI via `commands.py` |
| `cli.py` route | Enable `mytool report_generate` |
| Terminal feedback | Show progress and output folder |
| Command flags | Support `--summary-only`, `--pdf-only`, `--regenerate` (optional) |

---

## 🌐 API Task List

| Task | Description |
|------|-------------|
| `/report/generate` POST route | Triggers generation for active session |
| `/report/list` GET route | Returns list of generated reports from DB |
| `/report/{name}` GET route | Serves HTML/PDF file directly |
| `api.py` integrations | Wrap calls to `reporter.py` methods |
| Auth guard (optional) | Only allow admin roles to regenerate |

---

## 🧾 TUI Task List (Textual)

| Task | Description |
|------|-------------|
| Add `Reports` menu item | UI navigation to `Reports` panel |
| Enable generation from TUI | Button or command palette trigger |
| List generated reports | Pull from `lookups_snapshot_reports` |
| Open HTML viewer | Render HTML inside Textual viewer or open in browser |
| Show PDF download path | Give file path to user after generation |

---

## 🖥️ Dashboard Task List (Static Viewer)

| Task | Description |
|------|-------------|
| Read from `meta.json` | Build dynamic index of all reports |
| Show table of reports | Show name, date, type, HTML/PDF links |
| Render `index.html` | Master entry point to entire session site |
| Add breadcrumbs/navigation | Between summary, verify, mapping, etc. |
| Link reports into session view | Show full traceability per document |

---

## 🔁 Future-Proofing Options

| Feature | Benefit |
|--------|---------|
| `report_regenerate --snapshot {table_hash}` | Regenerate reports from snapshot |
| `template_versions` in metadata | Track version used for rendering |
| Tenant-based themes (style.css) | Branding per tenant |

---

Would you like the base scaffold for `core/reporter.py` next, with:

- `generate_all_reports()`
- `generate_snapshot_table()`
- `record_report_metadata()`
- `render_report(template_name, data_dict)`
- `convert_to_pdf(html_path)`

Ready to drop in? Say the word.