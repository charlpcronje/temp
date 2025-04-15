# DocTypeGen Validation System

## Overview

The validation system is responsible for:
1. Detecting document types by matching imported data against schemas
2. Validating data against schema rules
3. Generating field mappings between spreadsheet columns and schema fields
4. Providing detailed validation results and error reports

## Document Type Detection

The system automatically detects the document type by comparing the imported data against available schemas:

1. Each schema is loaded from the `schemas/` directory
2. Column names in the imported data are compared against field slugs in each schema
3. A match score is calculated for each schema based on:
   - Number of matching fields
   - Percentage of required fields matched
   - Data validation success rate
4. The schema with the highest match score is selected as the document type

## Validation Types

The system supports the following validation types:

### REGEX
Validates data against a regular expression pattern.

```json
{
  "validate_type": "REGEX",
  "regex": "^[A-Z0-9]{10}$"
}
```

### SA_ID_NUMBER
Validates South African ID numbers with checksum verification.

```json
{
  "validate_type": "SA_ID_NUMBER"
}
```

### BANK_ACCOUNT_NUMBER
Validates bank account numbers with format and checksum verification.

```json
{
  "validate_type": "BANK_ACCOUNT_NUMBER"
}
```

### DECIMAL_AMOUNT
Validates decimal amounts with optional currency symbols.

```json
{
  "validate_type": "DECIMAL_AMOUNT"
}
```

### UNIX_DATE
Validates and normalizes dates in various formats.

```json
{
  "validate_type": "UNIX_DATE"
}
```

### ENUM
Validates data against a list of allowed values.

```json
{
  "validate_type": "ENUM",
  "enum": "ALLOWED_VALUES_LIST_NAME"
}
```

### LEV_DISTANCE
Validates data using Levenshtein distance against a reference list.

```json
{
  "validate_type": "LEV_DISTANCE",
  "list": "REFERENCE_LIST_NAME",
  "distance": 80
}
```

### EMAIL
Validates email addresses.

```json
{
  "validate_type": "EMAIL"
}
```

### PHONE
Validates phone numbers in various formats.

```json
{
  "validate_type": "PHONE"
}
```

### NONE
No validation, accepts any value.

```json
{
  "validate_type": "NONE"
}
```

## Field Mapping

The field mapping process links spreadsheet columns to schema fields:

1. Initial mapping is generated automatically based on:
   - Column name matches with field slugs
   - Data validation success rates
   - Required field priorities
2. The mapping is stored in a JSON file: `mappings/{hash}_mapping.json`
3. Users can manually adjust mappings through the Web UI or API
4. The system validates mappings to ensure all required fields are mapped

### Mapping File Structure

```json
{
  "COLUMN_NAME": {
    "type": "FIELD_TYPE",
    "validate_type": "VALIDATION_TYPE",
    "required": true,
    "description": "Field description",
    "slug": ["FIELD_TYPE", "ALTERNATIVE_NAME"],
    "regex": "^[A-Z0-9]{10}$"
  }
}
```

## Validation Process

The validation process consists of the following steps:

1. **Schema Loading**: All schemas are loaded from the `schemas/` directory
2. **Document Type Detection**: The best matching schema is selected
3. **Field Mapping**: Columns are mapped to schema fields
4. **Data Validation**: Each row is validated against the schema rules
5. **Result Generation**: Validation results and error reports are generated

### Validation Results

Validation results include:

- Document type and match score
- Total rows, valid rows, and invalid rows
- Success rate percentage
- Field-level validation results
- Row-level validation errors
- Missing required fields

## Extending the Validation System

### Adding New Validation Types

1. Create a new validation class in `core/validator/validation_types/`:

```python
from .base import BaseValidator

class NewValidationType(BaseValidator):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize any specific properties
        
    def validate(self, value):
        # Implement validation logic
        if valid:
            return True, None
        else:
            return False, "Validation error message"
```

2. Register the new validation type in `core/validator/validation_types/__init__.py`:

```python
from .new_type import NewValidationType

VALIDATORS = {
    # Existing validators...
    "NEW_TYPE": NewValidationType,
}
```

### Adding New Schemas

1. Create a new schema file in the `schemas/` directory:

```json
{
  "type": "new_document_type",
  "template": "new_document_template.html",
  "output_doc_name": "{datetime}_{ID_NUMBER}_new_document.{HTML|PDF}",
  "schema": {
    "FIELD_1": {
      "slug": ["FIELD_1", "ALTERNATIVE_NAME"],
      "validate_type": "REGEX",
      "regex": "^[A-Z0-9]{10}$",
      "required": true,
      "description": "Field 1 description"
    },
    "FIELD_2": {
      "slug": ["FIELD_2"],
      "validate_type": "DECIMAL_AMOUNT",
      "required": false,
      "description": "Field 2 description"
    }
  }
}
```

2. Create a corresponding template in `templates/html/`:

```html
<!DOCTYPE html>
<html>
<head>
  <title>New Document Template</title>
  <link rel="stylesheet" href="../assets/style.css">
</head>
<body>
  <div class="document">
    <h1>New Document</h1>
    <div class="field">
      <label>Field 1:</label>
      <span>{{ record.FIELD_1 }}</span>
    </div>
    <div class="field">
      <label>Field 2:</label>
      <span>{{ record.FIELD_2 }}</span>
    </div>
  </div>
</body>
</html>
```

## Best Practices

### Schema Design

1. **Use Descriptive Field Names**: Choose clear, descriptive field names that reflect the data they represent.
2. **Include Alternative Slugs**: Add alternative slugs to improve column matching.
3. **Set Required Fields Carefully**: Only mark fields as required if they are truly necessary.
4. **Add Field Descriptions**: Include descriptions to help users understand the purpose of each field.
5. **Use Appropriate Validation Types**: Choose the most specific validation type for each field.

### Validation

1. **Start with Strict Validation**: Begin with strict validation rules and relax them if needed.
2. **Handle Edge Cases**: Consider edge cases in your validation rules (e.g., empty values, special characters).
3. **Provide Clear Error Messages**: Ensure validation error messages are clear and actionable.
4. **Test with Real Data**: Test validation rules with real-world data to ensure they work as expected.

### Field Mapping

1. **Review Automatic Mappings**: Always review automatically generated mappings for accuracy.
2. **Map All Required Fields**: Ensure all required fields are mapped before proceeding.
3. **Consider Data Types**: Ensure column data types are compatible with field validation types.
4. **Document Custom Mappings**: Document any custom mappings for future reference.
