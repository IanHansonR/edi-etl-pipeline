import logging
from typing import Optional


# SAFETY: Global flag for staging table mode
_STAGING_MODE = False


def initialize_staging_tables(db_connection):
    """
    SAFETY: Create or truncate staging tables for reprocess-all.
    Staging tables mirror production schema.
    """
    from database import execute_query
    
    logging.info("Initializing staging tables for reprocess-all")

    # Drop and recreate staging tables to ensure clean state
    execute_query(db_connection, """
        IF OBJECT_ID('EDI_Report_BOM_Component_Staging', 'U') IS NOT NULL
            DROP TABLE EDI_Report_BOM_Component_Staging
    """)

    execute_query(db_connection, """
        IF OBJECT_ID('EDI_Report_Detail_Staging', 'U') IS NOT NULL
            DROP TABLE EDI_Report_Detail_Staging
    """)

    execute_query(db_connection, """
        IF OBJECT_ID('EDI_Report_Header_Staging', 'U') IS NOT NULL
            DROP TABLE EDI_Report_Header_Staging
    """)

    # Create staging tables (no foreign keys for flexibility)
    execute_query(db_connection, """
        CREATE TABLE EDI_Report_Header_Staging (
            Id INT IDENTITY PRIMARY KEY,
            CustomerPO VARCHAR(50) NOT NULL,
            Company VARCHAR(100),
            StartDate DATE,
            CompleteDate DATE,
            Department VARCHAR(100),
            DownloadDate DATETIME NOT NULL,
            OrderDate DATETIME,
            POType VARCHAR(50),
            Version INT NOT NULL,
            SourceTableId INT,
            ProcessedDate DATETIME DEFAULT GETDATE(),

            INDEX IX_CustomerPO (CustomerPO),
            INDEX IX_CustomerPO_Version (CustomerPO, Version),
            INDEX IX_SourceTableId (SourceTableId)
        )
    """)

    execute_query(db_connection, """
        CREATE TABLE EDI_Report_Detail_Staging (
            Id INT IDENTITY PRIMARY KEY,
            HeaderId INT,
            Style VARCHAR(50),
            Color VARCHAR(50),
            Size VARCHAR(20),
            UPC VARCHAR(50),
            SKU VARCHAR(50),
            Qty INT,
            UOM VARCHAR(10),
            UnitPrice DECIMAL(18,4),
            RetailPrice DECIMAL(18,4),
            InnerPack INT,
            QtyPerInnerPack INT,
            DC VARCHAR(50),
            StoreNumber VARCHAR(50),
            IsBOM BIT,

            INDEX IX_HeaderId (HeaderId),
            INDEX IX_Style_Color (Style, Color)
        )
    """)

    execute_query(db_connection, """
        CREATE TABLE EDI_Report_BOM_Component_Staging (
            Id INT IDENTITY PRIMARY KEY,
            DetailId INT,
            ComponentSKU VARCHAR(50),
            ComponentSize VARCHAR(20),
            ComponentQty INT,
            ComponentUnitPrice DECIMAL(18,4),
            ComponentRetailPrice DECIMAL(18,4),

            INDEX IX_DetailId (DetailId)
        )
    """)

    logging.info("Staging tables created successfully")


def swap_staging_to_production(db_connection):
    """
    SAFETY: Atomic swap of staging tables to production.
    Uses table renaming for near-zero downtime.
    """
    from database import execute_query
    from security import sanitize_error_message
    
    logging.info("Beginning staging to production swap")

    # This is done in a transaction for atomicity
    execute_query(db_connection, "BEGIN TRANSACTION")

    try:
        # Rename production tables to backup
        execute_query(db_connection, """
            EXEC sp_rename 'EDI_Report_BOM_Component', 'EDI_Report_BOM_Component_Backup'
        """)
        execute_query(db_connection, """
            EXEC sp_rename 'EDI_Report_Detail', 'EDI_Report_Detail_Backup'
        """)
        execute_query(db_connection, """
            EXEC sp_rename 'EDI_Report_Header', 'EDI_Report_Header_Backup'
        """)

        # Rename staging tables to production
        execute_query(db_connection, """
            EXEC sp_rename 'EDI_Report_BOM_Component_Staging', 'EDI_Report_BOM_Component'
        """)
        execute_query(db_connection, """
            EXEC sp_rename 'EDI_Report_Detail_Staging', 'EDI_Report_Detail'
        """)
        execute_query(db_connection, """
            EXEC sp_rename 'EDI_Report_Header_Staging', 'EDI_Report_Header'
        """)

        execute_query(db_connection, "COMMIT TRANSACTION")
        logging.info("Staging tables successfully promoted to production")

        # Drop backup tables after successful swap
        execute_query(db_connection, "DROP TABLE EDI_Report_BOM_Component_Backup")
        execute_query(db_connection, "DROP TABLE EDI_Report_Detail_Backup")
        execute_query(db_connection, "DROP TABLE EDI_Report_Header_Backup")
        logging.info("Backup tables dropped")

    except Exception as e:
        execute_query(db_connection, "ROLLBACK TRANSACTION")
        logging.error(f"Failed to swap staging to production: {sanitize_error_message(e)}")
        raise


def swap_to_staging_mode():
    """
    SAFETY: Configure the ETL to write to staging tables.
    Returns original table names for restoration.
    """
    global _STAGING_MODE
    _STAGING_MODE = True
    logging.info("Switched to staging table mode")
    return True


def reset_staging_mode():
    """
    SAFETY: Reset staging mode flag back to production mode.
    Call this after reprocess-all completes (success or failure).
    """
    global _STAGING_MODE
    _STAGING_MODE = False
    logging.info("Reset to production table mode")


def get_table_name(base_name):
    """
    SAFETY: Get the appropriate table name (staging or production).
    """
    if _STAGING_MODE:
        return f"{base_name}_Staging"
    return base_name