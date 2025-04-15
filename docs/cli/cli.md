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

### `resolve_lookups` - Resolve Lookups for Generated Documents

Attempts to match generated document records with entities in the lookup database, populating references and identifiers.

**Arguments:**
- `session`: Hash of a specific session to process (optional)

**Example:**
```bash
python cli.py resolve_lookups
```

### `report_generate` - Generate Reports

Generates all available reports for the current session, including summary, mapping, verification, and exceptions reports in both HTML and PDF formats.

**Example:**
```bash
python cli.py report_generate
```

### `report_rerun` - Regenerate a Specific Report

Re-runs a previously generated report, which is useful for recreating reports after making changes to the underlying data.

**Arguments:**
- `report_id`: ID of the report to regenerate (required)

**Example:**
```bash
python cli.py report_rerun r-12345678
```

### `report_list` - List All Reports

Lists all report runs with their status and metadata.

**Example:**
```bash
python cli.py report_list
```

### `user` - User Management Commands

The `user` command group provides several subcommands for managing users in the system.

#### `user add` - Add a New User

Creates a new user in the system.

**Arguments:**
- `username`: Username for the new user (required)
- `password`: Password for the new user (required)

**Options:**
- `--role`: Role for the new user, either 'user' or 'admin' (default: 'user')

**Example:**
```bash
python cli.py user add john.doe password123 --role admin
```

#### `user list` - List All Users

Shows all users in the system with their roles, status, and other details.

**Example:**
```bash
python cli.py user list
```

#### `user password` - Change User Password

Updates a user's password.

**Arguments:**
- `username`: Username of the user to update (required)
- `new_password`: New password for the user (required)

**Example:**
```bash
python cli.py user password john.doe new_password123
```

#### `user role` - Change User Role

Changes a user's role in the system.

**Arguments:**
- `username`: Username of the user to update (required)
- `new_role`: New role for the user, either 'user' or 'admin' (required)

**Example:**
```bash
python cli.py user role john.doe admin
```

#### `user status` - Activate or Deactivate User

Activates or deactivates a user in the system.

**Arguments:**
- `username`: Username of the user to update (required)
- `is_active`: New status for the user, True for active, False for inactive (required)

**Example:**
```bash
python cli.py user status john.doe True
```

#### `user delete` - Delete a User

Removes a user from the system.

**Arguments:**
- `username`: Username of the user to delete (required)

**Options:**
- `--force, -f`: Force deletion without confirmation (default: False)

**Example:**
```bash
python cli.py user delete john.doe
python cli.py user delete jane.doe --force
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

## Shell Scripts

Let's create bash scripts for Linux and batch scripts for Windows to run these commands. The scripts will be stored in a 'scripts' folder but will change directory to the parent folder before execution.

### Linux Scripts (Bash)

Let's start with creating the bash scripts for Linux:

#### 1. `scripts/import.sh`

```bash
#!/bin/bash

# Change to parent directory
cd "$(dirname "$0")/.."

# Check if a file path was provided
if [ -z "$1" ]; then
  echo "Error: Please provide a file path."
  echo "Usage: ./scripts/import.sh <file_path> [options]"
  exit 1
fi

# Run the import command
python cli.py import "$@"

# Check if the command was successful
if [ $? -eq 0 ]; then
  echo "Import completed successfully."
  echo "You can now run validate.sh to continue."
else
  echo "Import failed. Please check the error message above."
fi
```

#### 2. `scripts/validate.sh`

```bash
#!/bin/bash

# Change to parent directory
cd "$(dirname "$0")/.."

# Run the validate command
python cli.py validate "$@"

# Check if the command was successful
if [ $? -eq 0 ]; then
  echo "Validation completed successfully."
  echo "You can now run map.sh to continue."
else
  echo "Validation failed. Please check the error message above."
fi
```

#### 3. `scripts/map.sh`

```bash
#!/bin/bash

# Change to parent directory
cd "$(dirname "$0")/.."

# Run the map command
python cli.py map "$@"

# Check if the command was successful
if [ $? -eq 0 ]; then
  echo "Mapping completed successfully."
  echo "You can now run html.sh to continue."
else
  echo "Mapping failed. Please check the error message above."
fi
```

#### 4. `scripts/html.sh`

```bash
#!/bin/bash

# Change to parent directory
cd "$(dirname "$0")/.."

# Run the html command
python cli.py html "$@"

# Check if the command was successful
if [ $? -eq 0 ]; then
  echo "HTML generation completed successfully."
  echo "You can now run pdf.sh to continue."
else
  echo "HTML generation failed. Please check the error message above."
fi
```

#### 5. `scripts/pdf.sh`

```bash
#!/bin/bash

# Change to parent directory
cd "$(dirname "$0")/.."

# Run the pdf command
python cli.py pdf "$@"

# Check if the command was successful
if [ $? -eq 0 ]; then
  echo "PDF generation completed successfully."
  echo "Processing workflow complete."
else
  echo "PDF generation failed. Please check the error message above."
fi
```

#### 6. `scripts/resolve_lookups.sh`

```bash
#!/bin/bash

# Change to parent directory
cd "$(dirname "$0")/.."

# Run the resolve_lookups command
python cli.py resolve_lookups

# Print a message
echo "Lookup resolution completed."
```

#### 7. `scripts/report_generate.sh`

```bash
#!/bin/bash

# Change to parent directory
cd "$(dirname "$0")/.."

# Run the report_generate command
python cli.py report_generate

# Print a message
echo "Reports generated successfully."
```

#### 8. `scripts/report_rerun.sh`

```bash
#!/bin/bash

# Change to parent directory
cd "$(dirname "$0")/.."

# Check if a report ID was provided
if [ -z "$1" ]; then
  echo "Error: Please provide a report ID."
  exit 1
fi

# Run the report_rerun command with the provided report ID
python cli.py report_rerun "$1"

# Print a message
echo "Report $1 regenerated successfully."
```

#### 9. `scripts/report_list.sh`

```bash
#!/bin/bash

# Change to parent directory
cd "$(dirname "$0")/.."

# Run the report_list command
python cli.py report_list

# Print a message
echo "Report listing completed."
```

#### 10. `scripts/all.sh`

```bash
#!/bin/bash

# Change to parent directory
cd "$(dirname "$0")/.."

# Check if a file path was provided
if [ -z "$1" ]; then
  echo "Error: Please provide a file path."
  echo "Usage: ./scripts/all.sh <file_path> [options]"
  exit 1
fi

# Run the all command
python cli.py all "$@"

# Check if the command was successful
if [ $? -eq 0 ]; then
  echo "Complete workflow completed successfully."
else
  echo "Workflow failed. Please check the error message above."
fi
```

#### 11. `scripts/list.sh`

```bash
#!/bin/bash

# Change to parent directory
cd "$(dirname "$0")/.."

# Run the list command
python cli.py list

echo "Use the scripts in the 'scripts' folder to run these commands."
```

#### 12. `scripts/setup-scripts.sh`

```bash
#!/bin/bash

# Make all scripts executable
chmod +x scripts/*.sh

echo "All scripts are now executable."
echo "You can run them using ./scripts/command.sh"
```

#### 13. `scripts/user_add.sh`

```bash
#!/bin/bash

# Change to parent directory
cd "$(dirname "$0")/.."

# Check if required arguments are provided
if [ $# -lt 2 ]; then
  echo "Error: Please provide username and password arguments."
  echo "Usage: $0 <username> <password> [role]"
  exit 1
fi

username=$1
password=$2
role=${3:-user}  # Default to 'user' if not specified

# Run the user add command
python cli.py user add "$username" "$password" --role "$role"

# Print a message
echo "User management command completed."
```

#### 14. `scripts/user_list.sh`

```bash
#!/bin/bash

# Change to parent directory
cd "$(dirname "$0")/.."

# Run the user list command
python cli.py user list

# Print a message
echo "User listing completed."
```

#### 15. `scripts/user_password.sh`

```bash
#!/bin/bash

# Change to parent directory
cd "$(dirname "$0")/.."

# Check if required arguments are provided
if [ $# -lt 2 ]; then
  echo "Error: Please provide username and new password arguments."
  echo "Usage: $0 <username> <new_password>"
  exit 1
fi

username=$1
new_password=$2

# Run the user password command
python cli.py user password "$username" "$new_password"

# Print a message
echo "Password change completed."
```

### Windows Scripts (Batch)

Now let's create equivalent batch scripts for Windows:

#### 1. `scripts/import.bat`

```batch
@echo off
setlocal

rem Change to parent directory
cd /d "%~dp0\.."

rem Check if a file path was provided
if "%~1"=="" (
  echo Error: Please provide a file path.
  echo Usage: scripts\import.bat ^<file_path^> [options]
  exit /b 1
)

rem Run the import command
python cli.py import %*

rem Check if the command was successful
if %ERRORLEVEL% equ 0 (
  echo Import completed successfully.
  echo You can now run validate.bat to continue.
) else (
  echo Import failed. Please check the error message above.
)

endlocal
```

#### 2. `scripts/validate.bat`

```batch
@echo off
setlocal

rem Change to parent directory
cd /d "%~dp0\.."

rem Run the validate command
python cli.py validate %*

rem Check if the command was successful
if %ERRORLEVEL% equ 0 (
  echo Validation completed successfully.
  echo You can now run map.bat to continue.
) else (
  echo Validation failed. Please check the error message above.
)

endlocal
```

#### 3. `scripts/map.bat`

```batch
@echo off
setlocal

rem Change to parent directory
cd /d "%~dp0\.."

rem Run the map command
python cli.py map %*

rem Check if the command was successful
if %ERRORLEVEL% equ 0 (
  echo Mapping completed successfully.
  echo You can now run html.bat to continue.
) else (
  echo Mapping failed. Please check the error message above.
)

endlocal
```

#### 4. `scripts/html.bat`

```batch
@echo off
setlocal

rem Change to parent directory
cd /d "%~dp0\.."

rem Run the html command
python cli.py html %*

rem Check if the command was successful
if %ERRORLEVEL% equ 0 (
  echo HTML generation completed successfully.
  echo You can now run pdf.bat to continue.
) else (
  echo HTML generation failed. Please check the error message above.
)

endlocal
```

#### 5. `scripts/pdf.bat`

```batch
@echo off
setlocal

rem Change to parent directory
cd /d "%~dp0\.."

rem Run the pdf command
python cli.py pdf %*

rem Check if the command was successful
if %ERRORLEVEL% equ 0 (
  echo PDF generation completed successfully.
  echo Processing workflow complete.
) else (
  echo PDF generation failed. Please check the error message above.
)

endlocal
```

#### 6. `scripts/resolve_lookups.bat`

```batch
@echo off
rem Change to parent directory
cd /d "%~dp0\.."

rem Run the resolve_lookups command
python cli.py resolve_lookups

rem Print a message
echo Lookup resolution completed.
pause
```

#### 7. `scripts/report_generate.bat`

```batch
@echo off
rem Change to parent directory
cd /d "%~dp0\.."

rem Run the report_generate command
python cli.py report_generate

rem Print a message
echo Reports generated successfully.
pause
```

#### 8. `scripts/report_rerun.bat`

```batch
@echo off
rem Change to parent directory
cd /d "%~dp0\.."

rem Check if a report ID was provided
if "%1"=="" (
  echo Error: Please provide a report ID.
  exit /b 1
)

rem Run the report_rerun command with the provided report ID
python cli.py report_rerun %1

rem Print a message
echo Report %1 regenerated successfully.
pause
```

#### 9. `scripts/report_list.bat`

```batch
@echo off
rem Change to parent directory
cd /d "%~dp0\.."

rem Run the report_list command
python cli.py report_list

rem Print a message
echo Report listing completed.
pause
```

#### 10. `scripts/all.bat`

```batch
@echo off
setlocal

rem Change to parent directory
cd /d "%~dp0\.."

rem Check if a file path was provided
if "%~1"=="" (
  echo Error: Please provide a file path.
  echo Usage: scripts\all.bat ^<file_path^> [options]
  exit /b 1
)

rem Run the all command
python cli.py all %*

rem Check if the command was successful
if %ERRORLEVEL% equ 0 (
  echo Complete workflow completed successfully.
) else (
  echo Workflow failed. Please check the error message above.
)

endlocal
```

#### 11. `scripts/list.bat`

```batch
@echo off
setlocal

rem Change to parent directory
cd /d "%~dp0\.."

rem Run the list command
python cli.py list

echo Use the scripts in the 'scripts' folder to run these commands.

endlocal
```

#### 12. `scripts/user_add.bat`

```batch
@echo off
rem Change to parent directory
cd /d "%~dp0\.."

rem Check if required arguments are provided
if "%1"=="" (
  echo Error: Please provide username and password arguments.
  echo Usage: %0 ^<username^> ^<password^> [role]
  exit /b 1
)

if "%2"=="" (
  echo Error: Please provide username and password arguments.
  echo Usage: %0 ^<username^> ^<password^> [role]
  exit /b 1
)

set username=%1
set password=%2
set role=%3

rem Default to 'user' if role not specified
if "%role%"=="" set role=user

rem Run the user add command
python cli.py user add "%username%" "%password%" --role "%role%"

rem Print a message
echo User management command completed.
pause
```

#### 13. `scripts/user_list.bat`

```batch
@echo off
rem Change to parent directory
cd /d "%~dp0\.."

rem Run the user list command
python cli.py user list

rem Print a message
echo User listing completed.
pause
```

#### 14. `scripts/user_password.bat`

```batch
@echo off
rem Change to parent directory
cd /d "%~dp0\.."

rem Check if required arguments are provided
if "%1"=="" (
  echo Error: Please provide username and new password arguments.
  echo Usage: %0 ^<username^> ^<new_password^>
  exit /b 1
)

if "%2"=="" (
  echo Error: Please provide username and new password arguments.
  echo Usage: %0 ^<username^> ^<new_password^>
  exit /b 1
)

set username=%1
set new_password=%2

rem Run the user password command
python cli.py user password "%username%" "%new_password%"

rem Print a message
echo Password change completed.
pause
```

## User Guide for Scripts

### Linux (Bash)

1. First, make the scripts executable:
   ```bash
   chmod +x scripts/*.sh
   ```
   Or run the setup script:
   ```bash
   ./scripts/setup-scripts.sh
   ```

2. To run a specific command, use the corresponding script:
   ```bash
   # Import a file
   ./scripts/import.sh path/to/data.csv
   
   # Validate the data
   ./scripts/validate.sh
   
   # Generate field mapping
   ./scripts/map.sh
   
   # Generate HTML files
   ./scripts/html.sh
   
   # Generate PDF files
   ./scripts/pdf.sh
   
   # Resolve lookups
   ./scripts/resolve_lookups.sh
   
   # Generate reports
   ./scripts/report_generate.sh
   
   # Regenerate a report
   ./scripts/report_rerun.sh r-12345678
   
   # List reports
   ./scripts/report_list.sh
   
   # Run all steps in sequence
   ./scripts/all.sh path/to/data.csv
   
   # List available commands
   ./scripts/list.sh
   
   # Add a new user
   ./scripts/user_add.sh john.doe password123
   
   # List all users
   ./scripts/user_list.sh
   
   # Change user password
   ./scripts/user_password.sh john.doe new_password123
   ```

### Windows (Batch)

1. Scripts can be run directly from Command Prompt or PowerShell:
   ```
   # Import a file
   scripts\import.bat path\to\data.csv
   
   # Validate the data
   scripts\validate.bat
   
   # Generate field mapping
   scripts\map.bat
   
   # Generate HTML files
   scripts\html.bat
   
   # Generate PDF files
   scripts\pdf.bat
   
   # Resolve lookups
   scripts\resolve_lookups.bat
   
   # Generate reports
   scripts\report_generate.bat
   
   # Regenerate a report
   scripts\report_rerun.bat r-12345678
   
   # List reports
   scripts\report_list.bat
   
   # Run all steps in sequence
   scripts\all.bat path\to\data.csv
   
   # List available commands
   scripts\list.bat
   
   # Add a new user
   scripts\user_add.bat john.doe password123
   
   # List all users
   scripts\user_list.bat
   
   # Change user password
   scripts\user_password.bat john.doe new_password123
   ```

## Tips for Using Scripts

1. **Step-by-Step Processing**: You can run each step sequentially as your data processing needs evolve.

2. **All-in-One Processing**: For simpler workflows, use the `all` script to run the complete process in one go.

3. **Passing Options**: You can pass additional options to any script:
   ```bash
   # Linux
   ./scripts/import.sh data.csv --force
   
   # Windows
   scripts\import.bat data.csv --force
   ```

4. **Custom Output Directory**: For the import script, you can specify a custom output directory:
   ```bash
   # Linux
   ./scripts/import.sh data.csv --output /custom/output/path
   
   # Windows
   scripts\import.bat data.csv --output C:\custom\output\path
   ```

5. **Viewing Results**: After processing, you can open the dashboard in your web browser:
   ```
   file:///path/to/output/[hash]/www/index.html
   ```

6. **Troubleshooting**: If a command fails, check the error messages. You might need to correct your data or mappings before proceeding.

These scripts streamline the document processing workflow, making it easier to run the commands with the correct working directory and arguments.