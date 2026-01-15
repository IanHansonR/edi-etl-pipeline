# Unit Testing Guide for EDI Parsing

This guide shows how to test the EDI parsing logic without connecting to a database.

## Quick Start

### Option 1: Run All Tests Automatically (Recommended)

Run the automated test suite:

```powershell
python run_tests.py
```

This will test all sample orders (PREPACK, BULK, minimal, and invalid) and show a summary.

### Option 2: Interactive Testing

Run the interactive test tool (requires user input):

```powershell
python sample_test_data.py
```

This will prompt you to run tests interactively.

### Option 3: Test Your Own JSON (Interactive)

```python
# Start Python interactive shell
python

# Import test functions
from test_transformers import test_edi_parsing, print_results

# Paste your JSON
json_input = """
{
  "PurchaseOrderHeader": {
    "PurchaseOrderNumber": "YOUR-PO-NUMBER",
    "CompanyCode": "YOUR-COMPANY",
    "PurchaseOrder": {
      "PurchaseOrderDetails": [
        ...
      ]
    }
  }
}
"""

# Run test
results = test_edi_parsing(json_input)

# Print table-formatted results
print_results(results)
```

### Option 4: Test from JSON File

```python
from test_transformers import run_test_from_file

# Test a JSON file
run_test_from_file('path/to/your/edi_data.json')
```

## Understanding the Output

The test output shows three sections:

### 1. Header Information
Shows the parsed purchase order header:
- Customer PO number
- Company code
- Dates (order, start, complete)
- Department
- Order type (PREPACK or BULK)
- Version number

### 2. Details Table
Shows all detail rows that would be inserted into `EDI_Report_Detail`:
- For BULK orders: One row per line item
- For PREPACK orders: One row per BOM unit (with `is_bom=True`)

### 3. BOM Components Table (PREPACK only)
Shows all BOM component rows that would be inserted into `EDI_Report_BOM_Component`:
- Component SKU, size, quantity, prices

## Example Output

```
✓ SUCCESS - Parsed PREPACK order
PO Number: 15826580
Version: 1

================================================================================
HEADER
================================================================================
customer_po         : 15826580
company             : KOHLS
order_date          : 2024-01-15 00:00:00
start_date          : 2024-02-01 00:00:00
complete_date       : 2024-02-15 00:00:00
department          : DEPT-123
download_date       : 2024-01-15 10:30:00
po_type             : PREPACK
version             : 1
source_table_id     : 1

================================================================================
DETAILS (2 rows)
================================================================================
Row  | style           | color           | size            | qty             | upc             | sku             | uom             | unit_price      | is_bom
--------------------------------------------------------------------------------------------------------------------
1    | STYLE-ABC       | Navy Blue       | None            | 100             | 00012345678905  | SKU-001         | EA              | 25.5            | True
2    | STYLE-XYZ       | Black           | None            | 50              | 00098765432105  | SKU-002         | EA              | 32.0            | True

================================================================================
BOM COMPONENTS (7 rows)
================================================================================
Row  | component_sku   | component_size  | component_qty   | component_unit_ | component_retai
--------------------------------------------------------------------------------------------------------------------
1    | 00012345678901  | S               | 20              | 25.5            | None
2    | 00012345678902  | M               | 40              | 25.5            | None
3    | 00012345678903  | L               | 30              | 25.5            | None
4    | 00012345678904  | XL              | 10              | 25.5            | None
5    | 00098765432101  | M               | 15              | 32.0            | None
6    | 00098765432102  | L               | 25              | 32.0            | None
7    | 00098765432103  | XL              | 10              | 32.0            | None

================================================================================
```

## Accessing Raw Results

The `test_edi_parsing()` function returns a dictionary with all parsed data:

```python
results = test_edi_parsing(json_input)

# Access specific parts
print(results['order_type'])          # 'PREPACK' or 'BULK'
print(results['customer_po'])         # PO number
print(results['header'])              # Header dictionary
print(results['details'])             # List of detail dictionaries
print(results['bom_components'])      # List of BOM component dictionaries

# Check for errors
if not results['success']:
    print(f"Error: {results['error']}")
```

## Testing Different Scenarios

### Test PREPACK Order
```python
from sample_test_data import SAMPLE_PREPACK_JSON
from test_transformers import test_edi_parsing, print_results

results = test_edi_parsing(SAMPLE_PREPACK_JSON)
print_results(results)
```

### Test BULK Order
```python
from sample_test_data import SAMPLE_BULK_JSON
from test_transformers import test_edi_parsing, print_results

results = test_edi_parsing(SAMPLE_BULK_JSON)
print_results(results)
```

### Test Error Handling
```python
from sample_test_data import SAMPLE_INVALID_JSON
from test_transformers import test_edi_parsing, print_results

results = test_edi_parsing(SAMPLE_INVALID_JSON)
print_results(results)
# Should show validation error
```

### Test Version Numbering
```python
from datetime import datetime

# Test multiple versions of same PO
json1 = """{"PurchaseOrderHeader": {...}}"""
json2 = """{"PurchaseOrderHeader": {...}}"""  # Same PO, different date

results1 = test_edi_parsing(json1, download_date=datetime(2024, 1, 1))
results2 = test_edi_parsing(json2, download_date=datetime(2024, 1, 2))

print(f"Version 1: {results1['version']}")  # Should be 1
print(f"Version 2: {results2['version']}")  # Should be 2
```

## Comparing to Database Schema

The output maps directly to your database tables:

**results['header']** → `EDI_Report_Header` table
- customer_po → CustomerPO
- company → Company
- order_date → OrderDate
- etc.

**results['details']** → `EDI_Report_Detail` table
- Each dictionary = one row
- is_bom flag indicates PREPACK vs BULK

**results['bom_components']** → `EDI_Report_BOM_Component` table
- Each dictionary = one row
- Only present for PREPACK orders

## Next Steps

Once your JSON tests pass successfully:

1. Verify the output matches your expected table structure
2. Validate field mappings are correct
3. Check date parsing and numeric conversions
4. Test with real EDI JSON from your system
5. When ready, connect to database using `main.py`
