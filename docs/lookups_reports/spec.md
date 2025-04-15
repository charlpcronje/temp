## ✅ MASTER REPORTING SYSTEM

### 🔹 1. 📄 **Report Purpose & Goals**

- Provides a full, auditable, and versioned view of a document generation session
- Tied to a snapshot of the source data
- Outputs portable static HTML and offline PDF reports
- Required before performing irreversible system changes (e.g., linking users, submitting records)
- Re-runnable and hash-verified for freshness

---

### 🔹 2. 📁 **Output Structure & Folder Layout**

```
output/{session_hash}/reports/hash{generated_{table_hash}}/
├── summary.html
├── summary.pdf
├── verify.html
├── verify.pdf
├── mapping.html
├── mapping.pdf
├── exceptions.html
├── exceptions.pdf
├── meta.json
├── style.css
```

Also mentioned:
- `html/` and `pdf/` folders remain for generated documents
- `www/index.html` should **link to the `reports/` page** or act as a gateway to them

---

### 🔹 3. 🗃️ **Database Tables (Schemas)**

#### ✅ `lookups_snapshot_{table_hash}`
- Full copy of `generated_{hash}` at time of report generation

#### ✅ `lookups_snapshot_reports`
| Column | Purpose |
|--------|---------|
| `report_id` | Unique report hash |
| `report_name`, `report_type` | e.g. `summary`, `verify`, etc. |
| `template_used` | Filename of report template |
| `html_file`, `pdf_file` | Output files |
| `path` | Folder output path |
| `source_hash`, `snapshot_table` | Traceability fields |
| `created_at` | When report was generated |

#### ✅ `report_runs`
Tracks one row per **batch** of reports:
| Column | Purpose |
|--------|---------|
| `report_id` | Unique ID used to re-run or query |
| `session_hash`, `table_hash` | What it was based on |
| `snapshot_table` | Name of the table frozen |
| `source_file` | Input file |
| `created_at`, `updated_at` | For stale checks |

#### Optional: `report_templates` (for versioned themes/templates)

---

### 🔹 4. 📌 **Report ID + Re-Run Logic**

- `report_id` generated per session (UUID or SHA of snapshot + config)
- `report_rerun --report_id abc123`
  - Re-calculates snapshot hash
  - If unchanged: return "✔ Reports still valid"
  - If changed: regenerate all reports under new `report_id`

---

### 🔹 5. 🧠 **Hashing Integrity & Freshness**

- Hash of `lookups_snapshot_{table_hash}` determines if rerun is needed
- Stored as `table_hash` in `report_runs`
- Must be recomputed on re-run requests

---

### 🔹 6. 🧾 **HTML Reports & Templates**

Each report consists of:
- Jinja2 or placeholder-based templates
- Rendered HTML
- Converted PDF
- Linked in `meta.json`

Template Types:
- `summary.jinja2`
- `verify.jinja2`
- `mapping.jinja2`
- `exceptions.jinja2`

---

### 🔹 7. 📥 **Centralized Command Definitions in `commands.py`**

**Command registry (`commands.py`)** must contain:
- `report_generate` – main entry point for generating reports
- `report_rerun` – re-run a previously generated report batch
- `report_list` – list all report runs
- All commands linked to `reporter.py` backend logic

This allows:
- Unified access from CLI, API, and TUI
- Central control of argument parsing, session validation, command metadata

---

### 🔹 8. ♻️ **Shared Report Logic in `reporter.py`**

All report actions (used by all interfaces) must call:
- `generate_all_reports()`
- `generate_snapshot_table()`
- `calculate_table_hash()`
- `convert_html_to_pdf()`
- `record_report_metadata()`
- `generate_meta_json()`

---

### 🔹 9. 🖨️ **PDF + Static Styling**

- All HTML reports must be converted to PDF
- Style copied into every output folder (`style.css`)
- Per-tenant styling can override default (if enabled in config)

---

### 🔹 10. 📊 **meta.json (Machine-Readable Summary)**

Located at:
```
output/{hash}/reports/hash{generated_{table_hash}}/meta.json
```

Contains:
- `report_id`
- `created_at`
- `snapshot_table`
- List of report files + metadata
- `source_hash`

---

### 🔹 11. 🔗 **Cross-Linking and Navigation**

- All HTML reports must:
  - Link back to `index.html`
  - Link to PDFs
  - Link to each other
  - Show breadcrumbs / navigation bar
- `index.html` should offer a unified view of the entire run

---

### 🔹 12. 🔁 **Interfaces That Trigger Report Generation**

| Interface | Triggers | Notes |
|-----------|----------|-------|
| CLI       | `report_generate`, `report_rerun`, `report_list` | Via `commands.py` |
| API       | `/report/generate`, `/report/rerun`, `/report/list` | Auth optional |
| TUI       | Button / Menu / Keyboard trigger | Shows report list + freshness |
| Dashboard | Lists report sets + links to HTML/PDF | Shows `report_id`, `valid?`, time, etc. |

All of these must trigger **the same shared report generation backend logic**.

---

### 🔹 13. 🧰 Optional Features

- TTL/expiration support for reports (not yet used)
- Template version tracking
- Tenant-specific theming
- Auto-regeneration if source changes detected (future feature)