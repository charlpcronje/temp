#!/usr/bin/env python

from core.mapper import update_mapping

def main():
    try:
        # Simulate the frontend's request format
        field_updates = {
            "field_updates": {
                "Company Name": {
                    "type": "COMPANY_NAME",
                    "validate_type": "LEV_DISTANCE",
                    "list": "COMPANY_NAME",
                    "distance": 80,
                    "required": True,
                    "slug": ["COMPANY_NAME", "COMPANY", "ISSUER"]
                },
                "Shareholder ID Number": {
                    "type": "SHAREHOLDER_ID_NUMBER",
                    "validate_type": "SA_ID_NUMBER",
                    "required": True,
                    "slug": ["SHAREHOLDER_ID_NUMBER", "ID_NUMBER", "ID"]
                }
            }
        }
        
        result = update_mapping(field_updates)
        print(f"Mapping updated successfully!")
        print(f"Number of mapped fields: {len(result)}")
        
        # Print the first few mappings
        for column, mapping in list(result.items())[:2]:
            print(f"  {column} -> {mapping['type']}")
    
    except Exception as e:
        print(f"Error updating mapping: {e}")

if __name__ == "__main__":
    main()
