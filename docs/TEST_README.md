# EDI Parsing Unit Tests - Quick Reference

Test the EDI parsing logic **without** connecting to a database.

## Files

- **[tests/run_tests.py](../tests/run_tests.py)** - Automated test runner (RECOMMENDED)
- **[tests/test_transformers.py](../tests/test_transformers.py)** - Core test framework with MockDatabase
- **[tests/sample_test_data.py](../tests/sample_test_data.py)** - Sample JSON data (PREPACK, BULK, etc.)
- **[tests/config_test.py](../tests/config_test.py)** - Test configuration (console logging, no file requirements)
- **[TESTING.md](TESTING.md)** - Full documentation

## Quick Start

### Run All Tests

```powershell
python tests/run_tests.py
```

Output shows:
- Header data that would go into `EDI_Report_Header`
- Detail rows that would go into `EDI_Report_Detail`
- BOM components that would go into `EDI_Report_BOM_Component`
- Test summary (PASS/FAIL)

### Test Your Own JSON

**Method 1: Interactive Paste (Easiest)**

```powershell
python tests/test_single.py
# Paste your JSON
# Type END on a new line when done
```

**Method 2: Python Interactive Shell**

```python
python

import sys
sys.path.insert(0, 'tests')
from test_transformers import test_edi_parsing, print_results

json_input = """
{
  "PurchaseOrderHeader": {
    "PurchaseOrderNumber": "YOUR-PO-HERE",
    ...
  }
}
"""

results = test_edi_parsing(json_input)
print_results(results)
```

**Method 3: From File**

```python
python

import sys
sys.path.insert(0, 'tests')
from test_transformers import run_test_from_file
run_test_from_file('path/to/your/edi_data.json')
```

## What Gets Tested

- ✓ JSON validation
- ✓ Order type detection (PREPACK vs BULK)
- ✓ Date parsing (YYYYMMDD format)
- ✓ Safe numeric conversions
- ✓ Header field extraction
- ✓ Detail row generation
- ✓ BOM component extraction (PREPACK orders)
- ✓ Version numbering logic
- ✓ Error handling

## Example Output

```
[SUCCESS] - Parsed PREPACK order
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
po_type             : PREPACK
version             : 1

================================================================================
DETAILS (2 rows)
================================================================================
Row  | style    | color      | qty  | upc            | sku     | is_bom
------------------------------------------------------------------------
1    | STYLE-ABC| Navy Blue  | 100  | 00012345678905 | SKU-001 | True
2    | STYLE-XYZ| Black      | 50   | 00098765432105 | SKU-002 | True

================================================================================
BOM COMPONENTS (7 rows)
================================================================================
Row  | component_sku  | component_size | component_qty
------------------------------------------------------
1    | 00012345678901 | S              | 20
2    | 00012345678902 | M              | 40
... (etc)
```

## Understanding Results

The returned dictionary contains:

```python
{
    'success': True,                    # Whether parsing succeeded
    'order_type': 'PREPACK' or 'BULK', # Detected order type
    'customer_po': '15826580',          # PO number
    'version': 1,                       # Version number
    'header': {...},                    # Header data (dict)
    'details': [{...}, {...}],          # Detail rows (list of dicts)
    'bom_components': [{...}, ...],     # BOM components (list of dicts)
    'summary': {
        'total_detail_rows': 2,
        'total_bom_components': 7
    }
}
```

## Next Steps

Once your JSON tests pass:

1. ✓ Verify output matches expected database structure
2. ✓ Test with real EDI JSON from your system
3. ✓ Validate field mappings are correct
4. ✓ Check date/numeric parsing
5. → Connect to database using `main.py`

## Troubleshooting

**Import Errors?**
- Make sure you're in the virtual environment: `.\venv\Scripts\Activate.ps1`
- Run from project root directory

**JSON Validation Failed?**
- Check that JSON has required fields: `PurchaseOrderHeader`, `PurchaseOrderNumber`, `CompanyCode`, `PurchaseOrder`, `PurchaseOrderDetails`

**Need More Details?**
- See [TESTING.md](TESTING.md) for comprehensive documentation
