import pyodbc
import logging

# SECURITY: Configure secure logging
logging.basicConfig(
    filename='C:\\EDI_Logs\\etl_process.log',  # Restricted directory
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# SECURITY: Separate logger for audit events
audit_logger = logging.getLogger('audit')
audit_handler = logging.FileHandler('C:\\EDI_Logs\\audit.log')
audit_handler.setFormatter(logging.Formatter('%(asctime)s - AUDIT - %(message)s'))
audit_logger.addHandler(audit_handler)
audit_logger.setLevel(logging.INFO)


class DatabaseConfig:
    """Centralized database configuration using Windows Authentication"""

    # SECURITY: Server names are not secrets - hardcode is fine
    SOURCE_SERVER = 'YOUR_SQL_SERVER'
    SOURCE_DATABASE = 'YourProductionDB'
    REPORTING_SERVER = 'YOUR_SQL_SERVER'
    REPORTING_DATABASE = 'YourReportingDB'

    @staticmethod
    def get_connection_string(db_type: str) -> str:
        """
        Get connection string using Windows Authentication (Trusted_Connection).
        SECURITY: No passwords in code or config files.
        """
        if db_type == 'source':
            server = DatabaseConfig.SOURCE_SERVER
            database = DatabaseConfig.SOURCE_DATABASE
        elif db_type == 'reporting':
            server = DatabaseConfig.REPORTING_SERVER
            database = DatabaseConfig.REPORTING_DATABASE
        else:
            raise ValueError(f"Unknown database type: {db_type}")

        # SECURITY: Windows Authentication only
        return (
            f"Driver={{ODBC Driver 17 for SQL Server}};"
            f"Server={server};"
            f"Database={database};"
            f"Trusted_Connection=yes;"
        )


def connect_to_database(db_type: str):
    """Establish database connection using Windows Authentication"""
    try:
        conn_string = DatabaseConfig.get_connection_string(db_type)
        connection = pyodbc.connect(conn_string)
        logging.info(f"Connected to {db_type} database successfully")
        return connection
    except Exception as e:
        # SECURITY: Log error but don't expose connection details
        logging.error(f"Failed to connect to {db_type} database: {type(e).__name__}")
        raise