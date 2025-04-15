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