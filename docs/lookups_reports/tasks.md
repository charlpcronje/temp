# Lookups Reports Tasks

- ✅ **Core (Shared Backend Logic)**
- ✅ **CLI**
- ✅ **TUI (Textual Interface)**
- ✅ **API**
- ✅ **Dashboard (Static + Dynamic Web Viewer)**

Each task list follows a production-level, modular format and is ready for delegation, tracking, or conversion into issues/stories.

---

# ✅ CORE BACKEND TASKS (`core/reporter.py`, `core/report_db.py`)

### 📁 Snapshot + Table Management
- [x] 1.1 `generate_snapshot_table(source_table_name)`  
  → Duplicates `generated_{hash}` into `lookups_snapshot_{table_hash}`
- [x] 1.2 `calculate_table_hash(table_name)`  
  → Returns consistent SHA256 hash of table contents
- [x] 1.3 `generate_report_id()`  
  → Generates UUID or hash-based report ID
- [x] 1.4 `report_table_exists(report_id)`  
  → Checks if snapshot + report already exists

### 📄 Report Rendering
- [x] 2.1 `render_report(template_name, data, output_path)`  
  → Renders report HTML from template and context
- [x] 2.2 `convert_html_to_pdf(html_path)`  
  → Generates PDF from HTML
- [x] 2.3 `generate_meta_json(report_id)`  
  → Stores metadata file summarizing report group
- [x] 2.4 `copy_style(target_folder)`  
  → Adds `style.css` to output for report set

### 🗃️ Database Management (`report_db.py`)
- [x] 3.1 `init_reporting_db()`  
  → Creates `report_runs`, `lookups_snapshot_reports`, etc.
- [x] 3.2 `record_report_run(report_id, session_hash, ...)`
- [x] 3.3 `record_report_file(report_id, report_name, report_type, ...)`

---

# ✅ CLI TASKS (`commands.py`, `cli.py`)

### 🔧 Command Registration
- [x] 4.1 Add `report_generate` to `COMMANDS` (no args)
- [x] 4.2 Add `report_rerun` with `--report_id`
- [x] 4.3 Add `report_list` to enumerate past runs

### 📦 CLI UX
- [x] 5.1 Show: `✔ Reports generated at ./output/{hash}/reports/{report_id}`
- [x] 5.2 Show stale/fresh status: `✔ Reports are up to date` or `🔁 Re-running due to data change`
- [x] 5.3 Include session context checks (status.json, hash present)

---

# ✅ TUI TASKS (Textual)

### 📊 Report UI
- [x] 6.1 Add `Reports` screen or menu entry
- [x] 6.2 List all `report_id` entries from `report_runs`
- [x] 6.3 Show `✔ Valid` / `❌ Stale` status
- [x] 6.4 Support "Generate Reports" and "Re-run" buttons

### 🧭 Report Viewer
- [x] 7.1 Open HTML report in TUI viewer or external browser
- [x] 7.2 Display metadata summary in panel
- [x] 7.3 Allow sorting by `created_at`, `report_type`, `status`

---

# ✅ API TASKS

### 🧩 Endpoints
- [x] 8.1 `POST /report/generate`  
  → Triggers full report run for active session
- [x] 8.2 `POST /report/rerun`  
  → Accepts `report_id`, performs hash comparison
- [x] 8.3 `GET /report/list`  
  → Lists all reports with metadata
- [x] 8.4 `GET /report/:report_id/html/:filename`  
  → Serves individual HTML file
- [x] 8.5 `GET /report/:report_id/pdf/:filename`  
  → Serves PDF file

### 🔐 Middleware
- [x] 9.1 Optional auth for generation and rerun routes
- [x] 9.2 Validate report ID and session context

---

# ✅ DASHBOARD TASKS (Static & Interactive)

### 🧷 Report Index View
- [x] 10.1 Load `meta.json` for each report group
- [x] 10.2 List:
  - `report_id`
  - `report_type`
  - `created_at`
  - `valid/invalid`
- [x] 10.3 Add "Download PDF" and "View HTML" buttons
- [x] 10.4 Add "Re-run Report" action (POST to `/report/rerun`)

### 🔗 Navigation & Styling
- [x] 11.1 Add breadcrumb navigation between:
  - `summary`, `mapping`, `verify`, `exceptions`
- [x] 11.2 Add sidebar or top bar for quick links
- [x] 11.3 Ensure `style.css` is loaded per report output

---

# 🧠 Optional Advanced Features

| Feature | System | Task |
|--------|--------|------|
| [ ] Template versioning | Core + DB | Add `report_templates` table, track per file |
| [ ] Stale warning in dashboard | Dashboard | Use table_hash to check report freshness |
| [ ] Theme override | All | Per-tenant `style.css` injected on render |
| [ ] Snapshot regeneration tool | CLI | `report_snapshot_rebuild --report_id` |