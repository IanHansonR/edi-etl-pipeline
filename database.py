import logging
from typing import Optional, List
from staging import get_table_name


def execute_query(connection, query: str, params: Optional[List] = None):
    """Execute parameterized query - SECURITY: Always use parameters"""
    cursor = connection.cursor()
    try:
        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        # Return results for SELECT queries
        if query.strip().upper().startswith('SELECT'):
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            return results
        else:
            connection.commit()
            # For INSERT with OUTPUT, return the generated ID
            if 'OUTPUT INSERTED.Id' in query.upper():
                row = cursor.fetchone()
                return [{'Id': row[0]}] if row else []
            return []
    except Exception as e:
        connection.rollback()
        # SECURITY: Don't expose query or parameters in error
        logging.error(f"Query execution failed: {type(e).__name__}: {str(e)[:200]}")
        raise
    finally:
        cursor.close()


def insert_header(customer_po, company, order_date, start_date, complete_date,
                 department, download_date, po_type, version, source_table_id,
                 db_connection):
    """
    Insert header record with versioning.
    SECURITY: Uses parameterized query.
    SAFETY: Writes to staging table if in reprocess-all mode.
    """
    table_name = get_table_name('EDI_Report_Header')

    query = f"""
        INSERT INTO {table_name} (
            CustomerPO, Company, OrderDate, StartDate, CompleteDate,
            Department, DownloadDate, POType, Version, SourceTableId, ProcessedDate
        )
        OUTPUT INSERTED.Id
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, GETDATE())
    """

    result = execute_query(db_connection, query, [
        customer_po, company, order_date, start_date, complete_date,
        department, download_date, po_type, version, source_table_id
    ])

    return result[0]['Id']


def insert_detail(header_id, style, color, size, qty, upc, sku, uom,
                 unit_price, retail_price, inner_pack, qty_per_inner_pack,
                 dc, store_number, is_bom, db_connection):
    """
    Insert detail record.
    SECURITY: Uses parameterized query.
    SAFETY: Writes to staging table if in reprocess-all mode.
    """
    table_name = get_table_name('EDI_Report_Detail')

    query = f"""
        INSERT INTO {table_name} (
            HeaderId, Style, Color, Size, Qty, UPC, SKU, UOM,
            UnitPrice, RetailPrice, InnerPack, QtyPerInnerPack,
            DC, StoreNumber, IsBOM
        )
        OUTPUT INSERTED.Id
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    result = execute_query(db_connection, query, [
        header_id, style, color, size, qty, upc, sku, uom,
        unit_price, retail_price, inner_pack, qty_per_inner_pack,
        dc, store_number, is_bom
    ])

    return result[0]['Id']


def insert_bom_component(detail_id, component_sku, component_size, component_qty,
                        component_unit_price, component_retail_price, db_connection):
    """
    Insert BOM component record.
    SECURITY: Uses parameterized query.
    SAFETY: Writes to staging table if in reprocess-all mode.
    """
    table_name = get_table_name('EDI_Report_BOM_Component')

    query = f"""
        INSERT INTO {table_name} (
            DetailId, ComponentSKU, ComponentSize, ComponentQty,
            ComponentUnitPrice, ComponentRetailPrice
        )
        VALUES (?, ?, ?, ?, ?, ?)
    """

    execute_query(db_connection, query, [
        detail_id, component_sku, component_size, component_qty,
        component_unit_price, component_retail_price
    ])


def insert_audit_log(db_connection, event_type: str, records_processed: int,
                     records_succeeded: int, records_failed: int, error_summary: Optional[str]):
    """Insert audit trail record"""
    query = """
        INSERT INTO EDI_ETL_AuditLog (
            EventType, RecordsProcessed, RecordsSucceeded, RecordsFailed,
            ErrorSummary, InitiatedBy
        )
        VALUES (?, ?, ?, ?, ?, SYSTEM_USER)
    """
    execute_query(db_connection, query, [
        event_type, records_processed, records_succeeded,
        records_failed, error_summary
    ])


def mark_processing_status(db_connection, source_id, status, error_message):
    """
    Update EDIGatewayInbound with processing status.
    SECURITY: Uses parameterized query.
    """
    query = """
        UPDATE EDIGatewayInbound
        SET ReportingProcessed = GETDATE(),
            ReportingProcessStatus = ?,
            ReportingProcessError = ?
        WHERE Id = ?
    """
    execute_query(db_connection, query, [status, error_message, source_id])


def mark_all_as_processed(db_connection):
    """
    Mark all EDI 850 records as successfully processed.
    SAFETY: Only called after successful reprocess-all completion.
    """
    query = """
        UPDATE EDIGatewayInbound
        SET ReportingProcessed = GETDATE(),
            ReportingProcessStatus = 'Success',
            ReportingProcessError = NULL
        WHERE TransactionType = '850'
        AND Status in ('downloaded', 'Obsolete')
    """
    execute_query(db_connection, query)
    logging.info("Marked all EDI 850 records as successfully processed")


def delete_existing_reporting_data(source_table_id, db_connection):
    """
    Delete existing reporting data for reprocessing.
    SECURITY: Uses parameterized queries to prevent injection.
    """
    # Get header ID(s) for this source record
    query = """
        SELECT Id FROM EDI_Report_Header
        WHERE SourceTableId = ?
    """
    headers = execute_query(db_connection, query, [source_table_id])

    for header in headers:
        # Delete BOM components first (foreign key constraint)
        execute_query(db_connection, """
            DELETE FROM EDI_Report_BOM_Component
            WHERE DetailId IN (
                SELECT Id FROM EDI_Report_Detail
                WHERE HeaderId = ?
            )
        """, [header['Id']])

        # Delete details
        execute_query(db_connection, """
            DELETE FROM EDI_Report_Detail
            WHERE HeaderId = ?
        """, [header['Id']])

        # Delete header
        execute_query(db_connection, """
            DELETE FROM EDI_Report_Header
            WHERE Id = ?
        """, [header['Id']])

    logging.info(f"Deleted existing reporting data for SourceTableId={source_table_id}")


def get_next_version_number(customer_po, download_date, db_connection):
    """
    Calculate version number based on chronological order of download dates.
    Versions are recalculated on reprocessing to maintain consistency.
    SECURITY: Uses parameterized query.
    SAFETY: Queries from staging table if in reprocess-all mode.
    """
    table_name = get_table_name('EDI_Report_Header')

    query = f"""
        SELECT COUNT(*) + 1 AS NextVersion
        FROM {table_name}
        WHERE CustomerPO = ?
        AND DownloadDate < ?
    """
    result = execute_query(db_connection, query, [customer_po, download_date])
    return result[0]['NextVersion']