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
├── output\{hash}_mapping.json                 # Column-to-type mapping overrides
schemas\{document_type}_schema.json
├── core/                     # Logic for import, validation, matching, reporting
├── public/                   # Hosted assets for dashboard
├── status.json               # Tracks the current session context
└── commands.py               # Central CLI command registry
```

status.json
```
{
  "last_updated": "2025-04-03T04:50:14.892085",
  "current_state": {
    "hash": "ce65e00a455ca83cf53c6a687daa45ff52c0cd6732deae7c682beb3e5b60bbb3",
    "sqlite_db_file": "output\\ce65e00a455ca83cf53c6a687daa45ff52c0cd6732deae7c682beb3e5b60bbb3\\data.db",
    "output_folder": "output\\ce65e00a455ca83cf53c6a687daa45ff52c0cd6732deae7c682beb3e5b60bbb3",
    "last_updated": "2025-04-03T04:50:14.892085",
    "last_operation": "VALIDATE_DATA",
    "imported_file": "test/pa.xlsx",
    "document_type": "payment_advice"
  }
}
---

status.json will tell you the document type and the sqite db path

## 🚀 Step-by-Step Usage/

---

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

This produces a {hash}_mapping.json` file. It maps your file’s columns to abstract field types (e.g. `email_address`, `amount`, `id_number`).

#### CLI
```bash
mytool map
```

---


I've now twice tried to update this with this way. Twice, I gave you all the instructions. Twice, you made assumptions. Twice, we regressed. We have made no progress. Nothing. We just regressed. No progress. It's cost me $50 so far, and I'm missing a deadline. 
- Point one, do not ever make assumptions. Ask for everything. Everything! Everything! 
- If you don't know how something works, then ask. 
- If you scan a file, scan the whole file. Don't miss anything. Because if you scan the files only half you only know half 
- Not assume anything.
- Do not do anything extra. 
- Never do anything extra. 
- Do not make assumptions. 

IMPORTANT.
Before you do any updats, you give me the plan short and to the point, if I could read zip format I would have asked you to zip you responsews,. I want it short.

Here is a background. In the root of the project, there is a status.json file.In that file, you will find the document_type, the sqlite database path, and the hash. Those are all important things. The hash is basically the session ID.
status.json
```
{
  "last_updated": "2025-04-03T04:50:14.892085",
  "current_state": {
    "hash": "ce65e00a455ca83cf53c6a687daa45ff52c0cd6732deae7c682beb3e5b60bbb3",
    "sqlite_db_file": "output\\ce65e00a455ca83cf53c6a687daa45ff52c0cd6732deae7c682beb3e5b60bbb3\\data.db",
    "output_folder": "output\\ce65e00a455ca83cf53c6a687daa45ff52c0cd6732deae7c682beb3e5b60bbb3",
    "last_updated": "2025-04-03T04:50:14.892085",
    "last_operation": "VALIDATE_DATA",
    "imported_file": "test/pa.xlsx",
    "document_type": "payment_advice"
  }
}
```

Then you will find the schema:  @payment_advice_schema.json check that this is being loaded dynamucallly and not hard coded. 
schemas\payment_advice_schema.json you get it's name dynamically by {document_type}_schema.json
You must open the entire schema, and not only the 200 lines, not 400 lines, everything, and understand what it says. Concentrate what it says. This is important. Do not just open it and scan through it. Read it. Understand it. Do not miss one field. Do not miss one key. 

Now, the problem that I'm having, when I go and I open a dashboard, which is located in the public folder, it's a React app, and it's running ShatCN. (public/src
)

The system has a few different sections. One is the API, one is the CLI, one is the TUI, and then it's got the dashboard. The API also hosts the dashboard, so when the React app is compiled, then the API serves the files. And how it works is it serves everything to the web-server part of the API, except if it's an API call endpoint, then it's supposed to be the endpoint. So keep in mind that there are a few loops, and React overlaps with those of the endpoints they will conflict

All the systems must use commands.py to make sure that it reads from there to know which commands are in the core of the system, so that the same functions are used throughout all the applications, so that it's not duplicated for every different interface.


TASKS

Then, from my dashboard, I click on "Step-by-Step Documents Generation." That takes me to a workflow.



- Then I click on Start Validation. 
- That takes me to a screen that I'm supposed to to validatevalidate the data based on the schema I referenced above. 
- And then it's supposed to generate a mapping file. If the mapping file already exists, then it doesn't immediately do any validation. 
- Then it skips the initial validation, and it just loads the screen. If you need to know something. Anything, ask me. Because this is ridiculous. I've been almost 10 hours, and I've just gone backwards. This is not happening again. You asked for everything..

Let me make this clear. The columns does not match up by column names. That's not what it's supposed to do. It must match up to the type. So what it does is, for you to know what column names there are, you must select that from the database, with the correct table name, and then you must create a schema for that table, which contains all the columns, and that's where you get the columns that you list on the left-hand side of the screen where I need to map the columns to the types. On the right-hand side, there must be an Edit button. If I click it, a dialog opens, and then I should be able to select only, nothing else, the type. The type is nicely in blocks. It's got the type name, and the validation type, and the description. I must be able to choose one for each row, and then I must be able to click Save. When I'm done with all that, I click Save on that page, and then I've got my types, and then I must be able to rerun the validation and see how it validates. That's where we have to be now. In 10 minutes, that must be done.