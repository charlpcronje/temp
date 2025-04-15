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