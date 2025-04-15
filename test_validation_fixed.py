#!/usr/bin/env python

from core.validator import validate_data

def main():
    try:
        result = validate_data()
        print(f"Validation completed successfully!")
        print(f"Document type: {result['validation_results']['document_type']}")
        print(f"Match score: {result['validation_results']['match_score']:.2f}%")
        print(f"Total rows: {result['validation_results']['total_rows']}")
        print(f"Valid rows: {result['validation_results']['valid_rows']}")
        print(f"Invalid rows: {result['validation_results']['invalid_rows']}")
        print(f"Success rate: {result['validation_results']['success_rate']:.1f}%")
        
        # Print all columns
        print("\nAll columns:")
        for col in result['all_columns']:
            print(f"  {col}")
        
        # Print field matches
        print("\nField matches:")
        for field_name, match_info in result['field_matches'].items():
            column = match_info.get('column', 'None')
            score = match_info.get('score', 0)
            match_type = match_info.get('match_type', 'none')
            print(f"  {field_name} -> {column} (score: {score:.2f}, type: {match_type})")
    
    except Exception as e:
        print(f"Error during validation: {e}")

if __name__ == "__main__":
    main()
