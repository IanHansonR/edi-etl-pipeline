# Usage Examples

## How to Use test_single.py

The `test_single.py` script lets you paste JSON and see the parsed output.

### Step-by-Step Instructions

1. **Run the script:**
   ```powershell
   python tests/test_single.py
   ```

2. **You'll see:**
   ```
   ================================================================================
   EDI JSON PARSER - INTERACTIVE TEST
   ================================================================================

   Paste your EDI JSON below.
   When finished, type END on a new line and press Enter.

   --------------------------------------------------------------------------------
   ```

3. **Paste your JSON** (you can copy from sample_test_data.py or use your own):
   ```
   {
     "PurchaseOrderHeader": {
       "PurchaseOrderNumber": "15826580",
       "CompanyCode": "KOHLS",
       ...paste the rest...
     }
   }
   ```

4. **Type `END` on a new line and press Enter:**
   ```
   END
   ```

5. **See the results!** The script will show:
   - Header data
   - Detail rows
   - BOM components (if PREPACK order)

### Example Session

```powershell
PS> python tests/test_single.py
================================================================================
EDI JSON PARSER - INTERACTIVE TEST
================================================================================

Paste your EDI JSON below.
When finished, type END on a new line and press Enter.

--------------------------------------------------------------------------------
{
  "PurchaseOrderHeader": {
    "PurchaseOrderNumber": "TEST-001",
    "CompanyCode": "TEST",
    "PurchaseOrder": {
      "PurchaseOrderDetails": [
        {
          "VendorItemNumber": "ITEM-123",
          "Quantity": 50
        }
      ]
    }
  }
}
END

================================================================================
PARSING JSON...
================================================================================

[SUCCESS] - Parsed BULK order
PO Number: TEST-001
Version: 1

================================================================================
HEADER
================================================================================
customer_po         : TEST-001
company             : TEST
...
```

## Quick Copy-Paste Test

Want to test quickly? Copy one of these complete JSON examples:

### Example 1: Simple BULK Order

Copy everything between the triple backticks:

```
{
  "PurchaseOrderHeader": {
    "PurchaseOrderNumber": "QUICK-TEST-001",
    "CompanyCode": "TESTCO",
    "PurchaseOrder": {
      "PurchaseOrderDetails": [
        {
          "VendorItemNumber": "WIDGET-100",
          "ColorDescription": "Red",
          "SizeDescription": "Medium",
          "Quantity": 100,
          "UnitPrice": 15.50
        }
      ]
    }
  }
}
```

Then:
1. Run `python tests/test_single.py`
2. Paste the JSON
3. Type `END` and press Enter

### Example 2: Use Sample Data

You can also copy from [sample_test_data.py](../tests/sample_test_data.py):

1. Open `tests/sample_test_data.py`
2. Find `SAMPLE_BULK_JSON` or `SAMPLE_PREPACK_JSON`
3. Copy the JSON content (without the triple quotes)
4. Paste into `test_single.py`
5. Type `END` and press Enter

## Alternative: Use Python Directly

If you prefer, use Python shell:

```python
python

import sys
sys.path.insert(0, 'tests')

# Import the sample data
from sample_test_data import SAMPLE_BULK_JSON
from test_transformers import test_edi_parsing, print_results

# Test it
results = test_edi_parsing(SAMPLE_BULK_JSON)
print_results(results)
```

This is even quicker if you're testing the sample data!

## Alternative: Test from File

If your JSON is in a file:

```python
python

import sys
sys.path.insert(0, 'tests')
from test_transformers import run_test_from_file
run_test_from_file('path/to/your/edi_data.json')
```
