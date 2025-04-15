## 📑 Specification: Database Tables

---

### ### 1. `lookups_snapshot_{table_hash}`

#### Purpose:
Stores an **immutable copy** of the data as it existed at the moment reports were generated. Every report is traceable to a frozen dataset.

#### Creation:
- Created by duplicating the active session table (named after the import hash)
- Data is inserted directly from that table
- No changes are made once created

> ✅ A new snapshot should only be created when report generation is triggered  
> ✅ The name must always be: `lookups_snapshot_<table_hash>`

#### Schema: _Dynamic_
- Exact structure mirrors the current session table (`generated_{table_hash}`)

---

### ### 2. `lookups_snapshot_reports`

#### Purpose:
Tracks every **report generation event**—which snapshot it used, what templates were applied, where the outputs were saved, and how to find those reports later (for reruns, auditing, downloads, etc.)

#### Table Name:
```sql
lookups_snapshot_reports
```

#### Schema:

```sql
CREATE TABLE lookups_snapshot_reports (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  report_id TEXT NOT NULL,             -- Unique identifier per report run (UUID or hash)
  snapshot_table TEXT NOT NULL,        -- e.g., lookups_snapshot_abc123
  report_name TEXT NOT NULL,           -- e.g., "Session Summary"
  report_type TEXT NOT NULL,           -- e.g., summary, verify, mapping, exceptions
  template_used TEXT NOT NULL,         -- Template filename
  path TEXT NOT NULL,                  -- Full output folder path
  html_file TEXT NOT NULL,             -- Generated HTML filename
  pdf_file TEXT NOT NULL,              -- Generated PDF filename
  source_hash TEXT NOT NULL,           -- Hash of original source file or session
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

### ### 3. `report_runs`

#### Purpose:
Tracks high-level **reporting events** (one row per generation session), allowing re-runs, metadata introspection, and reuse across UI components.

#### Table Name:
```sql
report_runs
```

#### Schema:

```sql
CREATE TABLE report_runs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  report_id TEXT UNIQUE NOT NULL,        -- Used for rerun reference
  session_hash TEXT NOT NULL,            -- The hash from status.json (imported file hash)
  snapshot_table TEXT NOT NULL,          -- e.g., lookups_snapshot_{table_hash}
  table_hash TEXT NOT NULL,              -- SHA256 hash of the snapshot table content
  source_file TEXT NOT NULL,             -- Original filename
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
  updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

### ### 4. Optional: `report_templates` (For template versioning / audit)

#### Table Name:
```sql
report_templates
```

#### Purpose:
If you allow templates to evolve or differ by tenant, this table tracks which version was used when.

```sql
CREATE TABLE report_templates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  template_name TEXT NOT NULL,
  version TEXT NOT NULL,
  description TEXT,
  last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 🧠 How These Tables Relate

```text
Import File (Excel/CSV)
     ↓
 Session Table → table_hash (e.g., 0abc123)
     ↓
 Snapshot Table = lookups_snapshot_0abc123
     ↓
 Reports (HTML, PDF)
     ↓
  ↳ Report ID (e.g., r-64cdee9a)
     ↳ report_runs (per generation session)
     ↳ lookups_snapshot_reports (per report file)
```

---

## 📂 Folder Linkage

Each row in `lookups_snapshot_reports` refers to:

```
output/{session_hash}/reports/hash{generated_{table_hash}}/
├── summary.html
├── summary.pdf
├── mapping.html
├── mapping.pdf
├── ...
```

The `path`, `html_file`, and `pdf_file` fields must together resolve the full location.

---

## 🔁 Re-run Report Logic

- `report_rerun --report_id abc123`
  - System looks up `report_runs.report_id`
  - Reads `snapshot_table` and rehashes it
  - If current hash matches `table_hash` → no-op
  - If changed → regenerates all reports
    - New entries are inserted into `lookups_snapshot_reports`
    - New row created in `report_runs`

---

Would you like the `CREATE TABLE` SQL for all of these wrapped into a Python function or migration utility? I can also produce a `report_db.py` manager with automatic table creation on first run.