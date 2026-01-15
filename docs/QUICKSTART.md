# Quick Start Guide

## For Testing (No Database Required)

### 1. Activate Virtual Environment
```powershell
.\venv\Scripts\Activate.ps1
```

### 2. Run Automated Tests
```powershell
python tests/run_tests.py
```

This tests PREPACK and BULK order parsing with sample data.

### 3. Test Your Own JSON

**Option A: Interactive Paste** (Easiest - See [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md))
```powershell
python tests/test_single.py
# 1. Paste your JSON
# 2. Type END on a new line
# 3. Press Enter
```

**Option B: Python Shell**
```python
python

import sys
sys.path.insert(0, 'tests')
from test_transformers import test_edi_parsing, print_results

json_input = """
{paste your JSON here}
"""

results = test_edi_parsing(json_input)
print_results(results)
```

**Option C: From File**
```python
python

import sys
sys.path.insert(0, 'tests')
from test_transformers import run_test_from_file
run_test_from_file('path/to/your/file.json')
```

### 4. Understand the Output

The test shows what would be inserted into each database table:

- **HEADER** section → `EDI_Report_Header` table
- **DETAILS** section → `EDI_Report_Detail` table
- **BOM COMPONENTS** section → `EDI_Report_BOM_Component` table (PREPACK only)

---

## For Production (Requires Database)

### 1. Configure Database Connections

Copy the template:
```powershell
cp config.example.py config.py
```

Edit [config.py](config.py) with your SQL Server details:
```python
if db_type == 'source':
    server = 'YOUR_SOURCE_SERVER'
    database = 'YOUR_SOURCE_DB'
elif db_type == 'reporting':
    server = 'YOUR_REPORTING_SERVER'
    database = 'YOUR_REPORTING_DB'
```

### 2. Create Database Tables

Run the SQL scripts from [edi_etl_implementation_plan_secure_v5.md](edi_etl_implementation_plan_secure_v5.md):

1. Alter `EDIGatewayInbound` (add processing status columns)
2. Create `EDI_Report_Header`
3. Create `EDI_Report_Detail`
4. Create `EDI_Report_BOM_Component`
5. Create `EDI_ETL_AuditLog`

### 3. Run ETL Pipeline

**Normal incremental processing:**
```powershell
python main.py
```

**Reprocess failed records:**
```powershell
python main.py --reprocess-failed
```

**Full rebuild (uses staging tables):**
```powershell
python main.py --reprocess-all
```

---

## File Reference

| File | Purpose |
|------|---------|
| [tests/run_tests.py](../tests/run_tests.py) | Run all automated tests |
| [tests/test_single.py](../tests/test_single.py) | Test a single JSON interactively |
| [tests/test_transformers.py](../tests/test_transformers.py) | Core test framework |
| [tests/sample_test_data.py](../tests/sample_test_data.py) | Sample JSON test data |
| [main.py](../main.py) | Production ETL entry point |
| [config.py](../config.py) | Database configuration (create from template) |
| [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) | Step-by-step usage examples |
| [TEST_README.md](TEST_README.md) | Testing quick reference |
| [TESTING.md](TESTING.md) | Complete testing documentation |
| [README.md](../README.md) | Full project documentation |

---

## Troubleshooting

**"No such file or directory: C:\\EDI_Logs"**
- You're trying to run production code without the log directory
- Use test scripts instead: `python tests/run_tests.py`

**Import errors**
- Activate virtual environment: `.\venv\Scripts\Activate.ps1`
- Install dependencies: `pip install -r requirements.txt`

**JSON validation failed**
- Check JSON has required fields: `PurchaseOrderHeader`, `PurchaseOrderNumber`, `CompanyCode`, `PurchaseOrder`, `PurchaseOrderDetails`
- Use sample data to compare structure: see [tests/sample_test_data.py](../tests/sample_test_data.py)

**Unicode errors in output**
- This is a Windows console encoding issue, the tests still work
- Results are still displayed correctly

**test_single.py keeps waiting for input**
- After pasting JSON, type `END` on a new line by itself
- Then press Enter
- See [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md) for detailed walkthrough

---

## Next Steps

1. ✓ Test with sample data → `python tests/run_tests.py`
2. ✓ Test with your real EDI JSON → `python tests/test_single.py`
3. ✓ Verify output matches expected table structure
4. → Set up database tables (SQL scripts in implementation plan)
5. → Configure [config.py](../config.py) with your database servers
6. → Run production ETL → `python main.py`
