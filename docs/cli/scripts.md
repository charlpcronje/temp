
## Scripts - User Guide for Scripts

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

# Run all steps in sequence
./scripts/all.sh path/to/data.csv

# List available commands
./scripts/list.sh
```

### Windows (Batch)

1. Scripts can be run directly from Command Prompt or PowerShell:
```sh
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

# Run all steps in sequence
scripts\all.bat path\to\data.csv

# List available commands
scripts\list.bat
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