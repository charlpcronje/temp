# 📘 Onboarding Guide: Using the Document Processing System (Phases 1–6)

_Last updated: April 2025_

---

## 🧭 Overview

This system ingests spreadsheet files (CSV/XLSX), determines their structure and document type, validates them against schemas, matches records to users in a tenant database, generates structured documents (HTML and PDF), and finally produces comprehensive reports capturing the process for review or audit.

---

## ✅ Prerequisites

- Python 3.10+
- `wkhtmltopdf` or `weasyprint` installed (for PDF generation)
- SQLite (used for session-based storage)
- A working `.env` file with at least:
  ```
  ENV=dev
  debug=true
  ```

---

## 🗂️ File & Folder Structure

```
project/
├── output/                   # All session-based outputs
│   └── {session_hash}/
│       ├── html/             # Generated HTML documents
│       ├── pdf/              # PDF versions
│       ├── www/              # Web dashboard
│       └── reports/          # Full audit reports (HTML + PDF)
├── config/{env}.json         # Environment-specific settings
├── mappings/                 # Column-to-type mapping overrides
├── core/                     # Logic for import, validation, matching, reporting
├── public/                   # Hosted assets for dashboard
├── status.json               # Tracks the current session context
└── commands.py               # Central CLI command registry
```

---

## 🚀 Step-by-Step Usage

---
## Create a user for yourself, this is to accesc the API and dashboard

```bash
# Add a new user
python cli.py user add jane.doe password123 --role user

# List all users
python cli.py user list

# Change a user's role
python cli.py user role jane.doe admin

# Change a user's password
python cli.py user password jane.doe new_password123

# Deactivate a user
python cli.py user status jane.doe False

# Delete a user
python cli.py user delete jane.doe
```

### 1️⃣ Import a New File

This begins the session. It hashes the file, imports it into SQLite, and updates `status.json`.

#### CLI
```bash
mytool import --file_path path/to/my_file.xlsx
```

#### API
```http
POST /import
Body: { "file_path": "path/to/my_file.xlsx" }
```

💬 **TODO**: Confirm actual CLI command name and flags  
💬 **TODO**: Confirm `/import` API endpoint (if available)

---

### 2️⃣ Validate the File

Determines which document type the file represents by comparing it to known schemas.

#### CLI
```bash
mytool validate
```

#### API
```http
POST /validate
```

💬 **TODO**: Confirm actual API endpoint and validation method

---

### 3️⃣ Generate Type Mapping File

This produces a `mappings/{hash}_mapping.json` file. It maps your file’s columns to abstract field types (e.g. `email_address`, `amount`, `id_number`).

#### CLI
```bash
mytool map
```

💬 **TODO**: Add equivalent API endpoint (e.g. `POST /mapping/generate`)

---

### 4️⃣ Resolve Lookups (User Matching)

This links records (e.g. via `id_number`) to known users in a tenant database.

#### CLI
```bash
mytool verify_users
```

💬 **TODO**: Confirm if this function is named `verify_users` or `resolve_users`

#### API
```http
POST /lookup/resolve
```

💬 **TODO**: Confirm actual endpoint, payload, and supported mappings

---

### 5️⃣ Generate Documents

Creates HTML + PDF documents for all validated and mapped rows.

#### CLI
```bash
mytool html
mytool pdf
```

💬 **TODO**: Confirm if both are required, or if `pdf` includes `html`

#### API
```http
POST /document/generate
```

💬 **TODO**: Confirm endpoint and whether batch or per-row generation is used

---

### 6️⃣ Generate Reports

This produces static HTML+PDF reports capturing everything processed in the session. A `report_id` is returned and stored for reruns or dashboard access.

#### CLI
```bash
mytool report_generate
```

#### API
```http
POST /report/generate
```

---

### 🔁 Re-Run Reports

Checks if the snapshot table has changed. If not, it reuses previous reports. If yes, it regenerates them.

#### CLI
```bash
mytool report_rerun --report_id abc123
```

#### API
```http
POST /report/rerun
Body: { "report_id": "abc123" }
```

---

### 📄 View Reports

Reports are saved in:
```
output/{session_hash}/reports/hash{generated_{table_hash}}/
```

Each report includes:
- `summary.html/pdf`
- `verify.html/pdf`
- `mapping.html/pdf`
- `exceptions.html/pdf`
- `meta.json`

You can view reports from:
- CLI: open folder manually
- TUI: view report list and preview
- Dashboard: reports listed under session or report tab
- API: download from `/report/{report_id}/html/:name`

💬 **TODO**: Confirm if static HTML is auto-mounted under `/static/reports/`

---

## 🧠 What Happens Behind the Scenes

- A frozen snapshot of the imported table is created:  
  `lookups_snapshot_{table_hash}`
- Reports use this snapshot to ensure repeatability
- A record is added to:
  - `report_runs` (per batch)
  - `lookups_snapshot_reports` (per report file)
- `meta.json` is generated with all paths and metadata

---

## 🧰 Debugging Tips

- Check `status.json` if the app says "no session found"
- Log files: `logs/app.log` or `output/{hash}/www/*.html`
- Snapshot table not found? You may need to re-run validation or import
- To reset everything: delete `status.json` and re-import

---

## ✅ Summary of Commands

| Phase        | CLI Command           | API Endpoint              |
|--------------|------------------------|----------------------------|
| Import       | `import`               | `POST /import`            |
| Validate     | `validate`             | `POST /validate`          |
| Map Types    | `map`                  | 💬 `POST /mapping/generate`? |
| Lookup       | `verify_users`         | `POST /lookup/resolve`    |
| Generate HTML| `html`                 | `POST /document/generate` |
| Generate PDF | `pdf`                  | (same)                    |
| Reports      | `report_generate`      | `POST /report/generate`   |
| Re-run Report| `report_rerun`         | `POST /report/rerun`      |