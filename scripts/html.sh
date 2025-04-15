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