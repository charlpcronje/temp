#!/bin/bash

# Change to parent directory
cd "$(dirname "$0")/.."

# Run the list command
python cli.py list

echo "Use the scripts in the 'scripts' folder to run these commands."