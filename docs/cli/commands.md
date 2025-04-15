# CLI Documentation and Script Utilities

I'll create comprehensive CLI documentation and script utilities for both Linux and Windows environments. These scripts will make it easy to run commands with proper arguments and working directories.

## Full CLI Documentation

Below is detailed documentation for each command available in the document processing system CLI:

### `import` - Import a CSV or Excel File

Imports a file into the system, creating a new processing session.

**Arguments:**
- `file_path`: Path to the CSV or Excel file to import (required)

**Options:**
- `--output, -o`: Custom output directory (optional)
- `--chunk-size, -c`: Number of rows to process at once for large files (default: 10000)
- `--force, -f`: Force reimport even if file was imported before (default: false)

**Example:**
```bash
python cli.py import data/payment_data.csv
```

### `validate` - Validate Imported Data

Validates the data in the current session against available schemas and determines the document type.

**Example:**
```bash
python cli.py validate
```

### `map` - Generate Field Mapping

Creates a mapping file that links data columns to schema fields.

**Example:**
```bash
python cli.py map
```

### `html` - Generate HTML Documents

Generates HTML files from the imported data using the appropriate template.

**Example:**
```bash
python cli.py html
```

### `pdf` - Generate PDF Documents

Converts HTML documents to PDF format for final output.

**Example:**
```bash
python cli.py pdf
```

### `all` - Run Complete Workflow

Executes all steps in sequence: import, validate, map, html, and pdf.

**Arguments:**
- `file_path`: Path to the CSV or Excel file to import (required)

**Example:**
```bash
python cli.py all data/payment_data.csv
```

### `list` - List Available Commands

Shows all available commands with their descriptions and arguments.

**Example:**
```bash
python cli.py list
```
