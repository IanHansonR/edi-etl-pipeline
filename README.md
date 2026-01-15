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
├── main.py              # Entry point
├── config.py            # Database configuration (not in git)
├── security.py          # Security utilities
├── etl_processor.py     # Core ETL logic
├── requirements.txt     # Python dependencies
└── README.md
```

## Security Notes
- Uses Windows Authentication (no passwords in code)
- All errors sanitized before logging
- Audit trail for all operations
- Never commit config.py with connection strings

## License
[Your chosen license]