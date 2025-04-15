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