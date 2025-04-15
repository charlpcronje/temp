# **Task List: Document Generation + Lookup Resolution System**

---

## 1. [x] **Implement Document Generation Logging**

1.1. [x] Create a function to insert a new record into `generated_{table_hash}` during HTML/PDF generation  
1.2. [x] Ensure the following fields are populated at generation time:
  - `document_type` (from `status.json → current_state.document_type`)
  - `mime_type` (`text/html` or `application/pdf`)
  - `input_file`, `row`, `data`
1.3. [x] Ensure the following fields remain **unset/null** at generation time:
  - `lookup_type`, `lookup`, `lookup_match`, `lookup_value`

---

## 2. [x] **Add Phase 2 Lookup Resolution Entry Points**

2.1. [x] Create a new **CLI command** in `commands.py` (e.g., `resolve_lookups`)  
2.2. [x] Create a new **TUI screen** for reviewing and triggering lookups  
2.3. [x] Add a new **API endpoint** (e.g., `POST /resolve-lookups`)  
2.4. [x] Add a new **Dashboard UI page** for managing lookups  

---

## 3. [x] **Build Lookup Execution Engine**

3.1. [x] Load unresolved rows from `generated_{table_hash}` (where `lookup_type IS NULL`)  
3.2. [x] Check `tenant.mappings[document_type]` to determine available lookup types:
  - If `column_to_column` exists, use it
  - If `type_to_column` exists, use it
3.3. [x] For each available mapping:
  - [x] Attempt the lookup
  - [x] Log the attempt to `tenant_lookup_{table_hash}`
3.4. [x] If a **match is found** (single result):
  - [x] Populate the following in `generated_{table_hash}`:
    - `lookup_type`
    - `lookup`
    - `lookup_match` (as `source_value:matched_value`)
    - `lookup_value` (matched foreign key)
3.5. [x] If **multiple matches** or **no match**:
  - [x] Log exception to `tenant_lookup_exceptions_{table_hash}`
  - [x] Do **not** update lookup fields in `generated_{table_hash}`

---

## 4. [x] **Log Lookup Attempts to `tenant_lookup_{table_hash}`**

4.1. [x] Create table schema for `tenant_lookup_{table_hash}`  
4.2. [x] Log one row per attempted mapping with:
  - `generated_id`
  - `action` description (e.g., `Tried column_to_column mapping X`)
  - `tenant_lookup_exceptions_id` (nullable)
  - `created_at`

---

## 5. [x] **Log Exceptions to `tenant_lookup_exceptions_{table_hash}`**

5.1. [x] Create table schema for `tenant_lookup_exceptions_{table_hash}`  
5.2. [x] For each failed or ambiguous lookup:
  - [x] Insert a row with:
    - `action`
    - `exception_message`
    - `input_file`
    - `row`
    - `data`
    - `lookup_value` (if applicable)
    - `accept_action` = `NULL`
    - `status` = `0`
    - `created_at` (timestamp)
5.3. [x] Link this exception to the lookup log (set `tenant_lookup_exceptions_id`)

---

## 6. [x] **Support Exception Review and Resolution**

6.1. [x] Allow exceptions to be manually reviewed and marked as resolved  
6.2. [x] When resolved:
  - [x] Set `accept_action` = `0` (rejected) or `1` (accepted)
  - [x] Set `status` = `1`
  - [x] Set `updated_at` = current timestamp
6.3. [x] If accepted:
  - [x] Update the corresponding row in `generated_{table_hash}` with:
    - `lookup_type`, `lookup`, `lookup_value`, `lookup_match`

---

## 7. [x] **Schema Management Utilities**

7.1. [x] Auto-create the following tables per `table_hash` if they do not exist:
  - `generated_{table_hash}`
  - `tenant_lookup_{table_hash}`
  - `tenant_lookup_exceptions_{table_hash}`
7.2. [x] Provide utility to cleanly regenerate these tables in dev mode

---

## 8. [x] **Unit + Integration Tests**

8.1. [x] Write tests for HTML/PDF generation logging  
8.2. [x] Write tests for lookup execution (both mapping types)  
8.3. [x] Write tests for exception logging  
8.4. [x] Write tests for manual exception resolution  
8.5. [x] Write tests to validate lookup value insertion into `generated_*`  
8.6. [x] Write regression tests for duplicate, missing, and invalid mappings