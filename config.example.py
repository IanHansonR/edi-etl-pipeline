"""
Configuration template - copy to config.py and fill in your values.
DO NOT commit config.py to git.
"""

import pyodbc
import logging

def connect_to_database(db_type):
    """
    Connect using Windows Authentication.
    
    db_type: 'source' or 'reporting'
    """
    if db_type == 'source':
        server = 'YOUR_SOURCE_SERVER'
        database = 'YOUR_SOURCE_DB'
    elif db_type == 'reporting':
        server = 'YOUR_REPORTING_SERVER'
        database = 'YOUR_REPORTING_DB'
    else:
        raise ValueError(f"Unknown db_type: {db_type}")
    
    conn_str = (
        f"Driver={{ODBC Driver 17 for SQL Server}};"
        f"Server={server};"
        f"Database={database};"
        f"Trusted_Connection=yes;"
    )
    
    return pyodbc.connect(conn_str)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Audit logger
audit_logger = logging.getLogger('audit')