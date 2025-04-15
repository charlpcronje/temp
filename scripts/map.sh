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