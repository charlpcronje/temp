#!/usr/bin/env python

from core.validator import validate_data
import json

def main():
    try:
        result = validate_data()
        
        # Print the result as JSON to see exactly what's being sent to the frontend
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Error during validation: {e}")

if __name__ == "__main__":
    main()
