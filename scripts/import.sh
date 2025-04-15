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