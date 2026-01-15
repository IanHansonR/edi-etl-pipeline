# EDI Reporting ETL Pipeline

Analytics ETL pipeline for processing EDI transmissions and building normalized reporting tables.

## Features
- Incremental ETL processing with change data capture
- Comprehensive error handling and retry logic
- Full audit trail and logging
- Staging table architecture for safe reprocessing
- Security-focused design (Windows Auth, sanitized errors)

## Setup

### Prerequisites
- Python 3.8+
- SQL Server with ODBC drivers
- Windows Authentication to source/target databases

### Installation

1. Clone the repository
```bash
git clone https://github.com/yourusername/edi-etl-pipeline.git
cd edi-etl-pipeline
```

2. Create virtual environment
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

3. Install dependencies
```powershell
pip install -r requirements.txt
```

4. Configure database connections (see Configuration section)

## Configuration

Create a `config.py` file with your database connection settings:
```python
# See config.example.py for template
```

## Testing (Without Database)

Test the parsing logic with sample or your own JSON data **before** connecting to a database:

```powershell
# Run all tests with sample data
python tests/run_tests.py

# Test a single JSON interactively
python tests/test_single.py
```

See [docs/TEST_README.md](docs/TEST_README.md) for complete testing guide or [docs/QUICKSTART.md](docs/QUICKSTART.md) to get started quickly.

## Usage

### Normal incremental processing
```powershell
python main.py
```

### Reprocess failed records only
```powershell
python main.py --reprocess-failed
```

### Full reprocessing (CAUTION)
```powershell
python main.py --reprocess-all
```

## Project Structure
```
Analytics_ETL_Pipeline/
├── tests/                         # Test files
│   ├── __init__.py
│   ├── run_tests.py               # Automated test runner
│   ├── test_single.py             # Interactive single JSON test
│   ├── test_transformers.py       # Unit test framework
│   ├── sample_test_data.py        # Sample JSON test data
│   └── config_test.py             # Test configuration (console logging)
├── docs/                          # Documentation
│   ├── QUICKSTART.md              # Quick start guide
│   ├── USAGE_EXAMPLES.md          # Usage examples
│   ├── TESTING.md                 # Complete testing guide
│   ├── TEST_README.md             # Testing quick reference
│   └── edi_etl_implementation_plan_secure_v5.md
├── main.py                        # Entry point for production
├── config.py                      # Database configuration (not in git)
├── config.example.py              # Configuration template
├── security.py                    # Security utilities
├── data_validation.py             # Safe data parsing functions
├── database.py                    # Database operations
├── etl_processor.py               # Core ETL orchestration
├── transformers.py                # Order-type specific logic
├── staging.py                     # Staging table management
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Security Notes
- Uses Windows Authentication (no passwords in code)
- All errors sanitized before logging
- Audit trail for all operations
- Never commit config.py with connection strings

## License
[Your chosen license]