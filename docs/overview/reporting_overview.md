## ✅ System Summary (Intro for Spec)

This system is a document processing and generation pipeline that ingests user-submitted data (typically via CSV or Excel), validates it against known schemas, enriches it with lookup-based matching logic, and ultimately produces standardized, styled HTML and PDF documents. The pipeline is designed to be fully automatable, interface-agnostic (CLI, API, TUI, Dashboard), and auditable at every stage.

---

### 🔹 **Step 1: Import & Session Setup**
The process begins by importing a file (CSV or XLSX), which is hashed and stored as a new session. Its contents are loaded into a SQLite database table named after the hash. This ensures that even repeated or updated versions of the same file are treated independently and retain audit traceability. The session hash is saved into `status.json` and used across all components to determine the current working context.

---

### 🔹 **Step 2: Data Validation Against Schemas**
Once imported, the system attempts to determine the **document type** (e.g., Payment Advice, Invoice) by checking which schema best matches the structure of the dataset. This is done by matching field types defined in the schemas against column contents in the dataset.

A separate `mapping.json` file is generated during this step, mapping each column in the source file to its inferred type (e.g., `id_number`, `email_address`, `company_name`). This abstraction layer ensures that document generation and downstream processing don’t depend on column names directly, which improves generalizability across diverse file formats.

---

### 🔹 **Step 3: Lookup Resolution (Entity Matching)**
The system then performs **lookup resolution**, which means connecting each row in the imported data to an existing user or entity in the tenant's database.

It uses the `type_to_column` configuration to map inferred field types (like `id_number`) from the dataset to known columns in the destination system (like `users.id_number` in MySQL). The system tries several mappings in order of priority.

- If **exactly one** match is found, it links the document to that user.
- If **zero or multiple** matches are found, the row is flagged as an **exception**.

This lookup logic is powerful and flexible, allowing per-tenant customization and resolution across local and remote systems (SQLite, MySQL, AWS-hosted MySQL, etc.).

---

### 🔹 **Step 4: Exception Management**
Unresolved lookups (exceptions) are captured for review. These may include:
- Rows where `id_number` or `email_address` was missing or ambiguous
- Columns that couldn't be mapped to known types
- Failed validation due to missing fields required by the schema

These unresolved cases block document finalization or user delivery, and must be addressed before moving forward. They're presented clearly in reports for resolution.

---

### 🔹 **Step 5: Document Generation (HTML & PDF)**
With validation and entity resolution complete, the system uses a predefined HTML template (per document type) to generate:
- One HTML document per valid row
- A PDF version of each HTML file

These documents are styled using a configurable or per-tenant `style.css`. Output is placed in a structured `output/{hash}/` directory, grouped by format (`html/`, `pdf/`) and session.

---

### 🔹 **Step 6: Reporting System (This Phase)**
At this stage, before any final submission to the downstream systems (like ShareHub), the system performs a full report generation step. This creates a **frozen snapshot** of the dataset (`lookups_snapshot_{table_hash}`), then generates a complete set of reports that reflect the session state:

- **summary.html/pdf** – overall session status and document type
- **mapping.html/pdf** – field mappings, inference results, unmatched columns
- **verify.html/pdf** – lookup matches and user binding status
- **exceptions.html/pdf** – all unresolved lookups and data issues

Each report run is uniquely identified by a `report_id` and includes both HTML and PDF formats. The reports are traceable, re-runnable, and validated against the snapshot hash to prevent stale state. This ensures full auditability, reusability, and structured handoff to both human reviewers and external systems.

---

### 🔹 **Why These Reports Are Critical**
These reports act as a **checkpoint** and **compliance layer**:

- They **prove** what data was processed
- They **log** what decisions were made (e.g., why a user was matched)
- They offer a **static archive** for audits and offline access
- They ensure **consistency** between what was validated and what will be submitted or shared
- They support **UI-driven workflows** by being viewable in a dashboard, downloadable from the API, and renderable in the TUI or CLI