# 📄 Module Documentation: `Document Generation & Lookup Resolution`

## Index

- [Specification](./spec.md)
- [Tasks to Implement](./tasks.md)
- [Dashboard](../dashboard/lookups.md)
- [Tasks to Implement](../dashboard/lookups_tasks.md)

## Overview

This module is responsible for:

- Generating HTML and PDF documents from imported rows
- Logging each generated document into a per-import SQLite table (`generated_{table_hash}`)
- Performing **deferred lookup resolution** to match each row to a unique foreign key
- Logging **every attempted lookup** and **all exceptions**
- Supporting manual resolution of ambiguous lookups

The system is designed for **full auditability**, **separation of responsibilities**, and **traceable data lineage**.

---

## 🔁 Workflow

### Phase 1: Document Generation

- Triggered by the **existing generation pipeline**
- Renders an HTML and/or PDF file per row
- Logs output metadata into `generated_{table_hash}`
- **Does not perform any lookups**
- Fields like `lookup_type`, `lookup_value`, etc., are left empty

### Phase 2: Lookup Resolution

- Triggered via:
  - New **CLI command** in `commands.py`
  - New **TUI screen**
  - New **dashboard page**
  - New **API endpoint** (e.g. `POST /resolve-lookups`)
- This phase:
  - Attempts to resolve a foreign key for each row
  - Logs every lookup attempt to `tenant_lookup_{table_hash}`
  - Logs all failures to `tenant_lookup_exceptions_{table_hash}`
  - Updates the original `generated_{table_hash}` row if successful or resolved manually

---

## 📦 Tables Created Per Import

### 1. `generated_{table_hash}`

Stores all generated HTML/PDF records.

| Column           | Description |
|------------------|-------------|
| `id`             | Auto-incremented primary key |
| `document_type`  | Value from `status.json → current_state.document_type` |
| `mime_type`      | `"text/html"` or `"application/pdf"` |
| `input_file`     | Name of imported file |
| `row`            | Row number |
| `data`           | Full row as JSON |
| `lookup_type`    | `"column_to_column"` or `"type_to_column"` (set later) |
| `lookup`         | Mapping string used for match |
| `lookup_match`   | `"input_value:match_value"` |
| `lookup_value`   | The matched foreign key |
| `created_at`     | Timestamp |

> Rows start incomplete. Lookup values are filled in **only after resolution is complete or an exception is resolved**.

---

### 2. `tenant_lookup_{table_hash}`

Logs **every lookup attempt**, whether successful or not.

| Column                      | Description |
|-----------------------------|-------------|
| `id`                        | Auto-incremented |
| `generated_id`              | Foreign key to `generated_*` row |
| `action`                    | Description of the attempted lookup |
| `tenant_lookup_exceptions_id` | If triggered, ID from exceptions table |
| `created_at`                | Timestamp of the attempt |

> Multiple lookup rows may exist per generated row — all attempts must be logged.

---

### 3. `tenant_lookup_exceptions_{table_hash}`

Tracks lookups that fail or return ambiguous results.

| Column              | Description |
|---------------------|-------------|
| `id`                | Primary key |
| `action`            | Description of the failure |
| `exception_message` | Exception raised |
| `input_file`        | Imported file name |
| `row`               | Row number |
| `data`              | JSON data of the row |
| `accept_action`     | NULL = pending, 0 = rejected, 1 = accepted |
| `lookup_value`      | Unmatched value |
| `status`            | 0 = unresolved, 1 = resolved |
| `created_at`        | UNIX timestamp |
| `updated_at`        | UNIX timestamp |

> Manual resolution updates `status` and populates the missing values back into `generated_*`.

---

## 🧠 Lookup Behavior

### Mapping Format

Mappings are declared under:

```json
tenant.mappings[payment_advice].column_to_column
tenant.mappings[payment_advice].type_to_column
```

Examples:

```txt
local_sqlite:imported_ce65e00a455:'Shareholder ID Number' = local_mysql:users:email
local_sqlite:imported_ce65e00a455:SA_ID_NUMBER = local_mysql:users:email
```

### Column-Based Lookup

Matches by column name in source and target tables.

### Type-Based Lookup

Uses validated **types** (e.g. `"SA_ID_NUMBER"`) mapped to source column names via:

```json
{
  "SHAREHOLDER_ID_NUMBER": {
    "column": "Shareholder ID Number",
    "type": "SA_ID_NUMBER"
  }
}
```

---

## 🧪 Lookup Execution Process

For each generated row:

1. Check which lookup types are available (`column_to_column`, `type_to_column`)
2. For each candidate mapping under that type:
   - Attempt match
   - Log to `tenant_lookup_*`
   - If exception: log to `tenant_lookup_exceptions_*`
3. If match is found:
   - Update `generated_*` with:
     - `lookup_type`
     - `lookup`
     - `lookup_value`
     - `lookup_match`
4. If exception is **manually resolved**:
   - Update exception row
   - Update original `generated_*` row
5. If unresolved:
   - Leave row incomplete
   - Escalate for entity creation (outside scope)

---

## 💡 Design Principles

- 🔄 **Separation of responsibilities**: generation and lookup are distinct
- 📈 **Traceability**: every action is logged
- ⚠️ **Resilience**: lookup failures are handled gracefully
- 🧑‍⚖️ **Human-in-the-loop**: exceptions can be manually resolved
- 🔌 **Modular**: each phase can be run, retried, or scaled independently

---

## ✅ Final Notes

This module is production-ready and fully auditable. Lookup resolution is **not coupled** to document generation, enabling async and human-supervised workflows. Exceptions do not block generation, and logging ensures clear visibility into system behavior.

## TTS Version
- **[lookups.aac](lookups.aac click to download)**

Once the HTML and PDF documents are generated in **Step 3**, the system stores basic metadata for each generated file in a dedicated SQLite table called `generated_{table_hash}`. This includes information like the document type, MIME type, input file name, row number, and the original row data in JSON format. However, at this point, no lookups have been performed yet. The fields related to lookup resolution — such as `lookup_type`, `lookup`, `lookup_value`, and `lookup_match` — are deliberately left empty. These fields will be populated later during the next phase of the process.

The actual lookup phase must happen in a **completely separate step**. This is critical for keeping the generation lightweight and ensuring that all data resolution logic is traceable, auditable, and repeatable. The lookup phase must be exposed through a new command in the CLI (specifically in `commands.py`), a new screen in the TUI interface, a new page on the admin dashboard, and a dedicated API endpoint. This allows the lookup process to be manually initiated, reviewed, or automated independently of document generation. It also enables batch resolution and provides full control over when and how data matching is performed.

During this phase, the system will iterate through each row in the `generated_*` table that does not yet have lookup information filled in. For each row, it checks which type of mapping is available — either `column_to_column` or `type_to_column`. It then attempts **all** candidate mappings listed under the available mapping type. Importantly, the system does **not stop at the first match**. Instead, it runs all possible lookup paths and records each attempt.

Every lookup attempt is logged in a separate table called `tenant_lookup_{table_hash}`. This table records the generated row ID, a description of the action taken, and optionally, a link to an exception if the lookup failed. Whether the lookup succeeds, fails, or produces multiple matches, it is always logged — nothing is skipped. This ensures that every data resolution attempt is traceable, regardless of the outcome.

If a lookup fails, either because there’s no match or because it returns more than one result, the system logs an exception to another table called `tenant_lookup_exceptions_{table_hash}`. This exception table stores the full context — including the failed action, a system-generated error message, the original row data, the input file name, and the row number. It also includes fields like `accept_action`, `status`, and timestamps for when the exception was raised and when it was resolved. These exceptions are meant to be reviewed by a human, either for correction or for approval in cases where the match can be trusted even though it didn’t pass the automated checks.

Once a match is confirmed — either automatically or through manual resolution of an exception — the system then updates the original row in `generated_{table_hash}`. It fills in the lookup type, the mapping that was used, the value that was looked up, and the final match that was found. If no valid match is ever found and no exception is resolved, the row remains incomplete. These unresolved cases must be escalated, potentially requiring a new entity to be created manually in the target database. That escalation process is outside the scope of this module but is anticipated as a downstream requirement.

To summarize, the lookup phase is deliberately decoupled from generation. Every attempt is logged. Every failure is explained. Every resolution is explicit. This design guarantees full traceability, repeatability, and auditability, while also supporting human oversight and complex edge cases. This is a robust foundation for scaling both automation and trust in document-data alignment.