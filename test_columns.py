#!/usr/bin/env python

from core.validator import validate_data

def main():
    try:
        result = validate_data()
        print(f"Validation completed successfully!")
        
        # Print all keys in the result
        print("\nResult keys:")
        for key in result.keys():
            print(f"  {key}")
        
        # Print all columns if available
        if 'all_columns' in result:
            print("\nAll columns:")
            for col in result['all_columns']:
                print(f"  {col}")
        else:
            print("\nNo 'all_columns' field in the result!")
    
    except Exception as e:
        print(f"Error during validation: {e}")

if __name__ == "__main__":
    main()
