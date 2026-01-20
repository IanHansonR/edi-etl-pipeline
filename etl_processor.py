import json
import logging
from config import audit_logger
from security import sanitize_error_message, log_audit_event, validate_json_structure
from database import (execute_query, mark_processing_status, mark_all_as_processed, 
                     delete_existing_reporting_data, get_next_version_number, insert_audit_log)
from transformers import detect_order_type, process_prepack_order, process_bulk_order
from staging import (initialize_staging_tables, swap_to_staging_mode, reset_staging_mode,
                    swap_staging_to_production)


def process_edi_transmissions(source_db_connection, target_db_connection, reprocess_all=False):
    """
    Process EDI 850 transmissions from EDIGatewayInbound.
    SECURITY: Comprehensive error handling and audit logging.

    SAFETY: When reprocess_all=True, uses staging tables to ensure atomic rebuild.
    Never deletes production data until new data is successfully loaded.

    Args:
        reprocess_all: If True, reprocess ALL records into staging tables, then swap
                      If False, only process new/failed records into production tables
    """

    # SAFETY: For reprocess-all, use staging tables
    if reprocess_all:
        audit_logger.warning("REPROCESS-ALL mode initiated - will rebuild via staging tables")
        logging.warning("REPROCESS-ALL: Building new dataset in staging tables before swapping")

        # Create/truncate staging tables
        initialize_staging_tables(target_db_connection)

        # Override table names to use staging
        swap_to_staging_mode()

    # Initialize variables OUTSIDE try block to ensure they exist even if query fails
    success_count = 0
    failure_count = 0
    error_summary = []
    edi_records = []

    try:
        # Build query based on reprocess flag
        if reprocess_all:
            where_clause = """
                WHERE TransactionType = '850'
                AND Status in ('downloaded', 'Obsolete')
            """
        else:
            where_clause = """
                WHERE TransactionType = '850'
                AND Status in ('downloaded', 'Obsolete')
                AND (ReportingProcessStatus IS NULL OR ReportingProcessStatus = 'Failed')
            """

        query = f"""
            SELECT
                Id,
                Created AS DownloadDate,
                CompanyCode,
                Channel,
                TransactionType,
                JSONContent,
                ReportingProcessStatus,
                ReportingProcessed
            FROM EDIGatewayInbound
            {where_clause}
            ORDER BY Created ASC
        """

        edi_records = execute_query(source_db_connection, query)
        logging.info(f"Retrieved {len(edi_records)} records for processing")

        # Main processing loop
        for record in edi_records:
            try:
                # SAFETY: No deletion in reprocess-all mode - building fresh in staging
                # For incremental mode, delete only if updating existing record
                if not reprocess_all and record['ReportingProcessStatus'] == 'Success':
                    # This is a re-run of previously successful record (rare edge case)
                    delete_existing_reporting_data(
                        record['Id'],
                        target_db_connection
                    )

                # SECURITY: Parse and validate JSON
                try:
                    edi_data = json.loads(record['JSONContent'])
                except json.JSONDecodeError as e:
                    raise ValueError(f"Invalid JSON content: {sanitize_error_message(e)}")

                # SECURITY: Validate JSON structure before processing
                validate_json_structure(edi_data)

                # Extract PO number (SECURITY: validated in validate_json_structure)
                customer_po = edi_data['PurchaseOrderHeader']['PurchaseOrderNumber']

                # Calculate version number
                version = get_next_version_number(
                    customer_po,
                    record['DownloadDate'],
                    target_db_connection
                )

                # Detect order type
                order_type = detect_order_type(edi_data)

                # Process based on type
                if order_type == 'PREPACK':
                    process_prepack_order(
                        edi_data=edi_data,
                        download_date=record['DownloadDate'],
                        source_table_id=record['Id'],
                        version=version,
                        db_connection=target_db_connection
                    )
                else:
                    process_bulk_order(
                        edi_data=edi_data,
                        download_date=record['DownloadDate'],
                        source_table_id=record['Id'],
                        version=version,
                        db_connection=target_db_connection
                    )

                # Mark as successfully processed (only in incremental mode)
                if not reprocess_all:
                    mark_processing_status(
                        source_db_connection,
                        record['Id'],
                        status='Success',
                        error_message=None
                    )

                success_count += 1
                # SECURITY: Don't log sensitive PO details, just identifiers
                logging.info(f"✓ Processed PO {customer_po} v{version} (ID={record['Id']})")

            except Exception as e:
                # SECURITY: Sanitize error message before storing
                error_msg = sanitize_error_message(e)

                # Mark as failed (only in incremental mode)
                if not reprocess_all:
                    mark_processing_status(
                        source_db_connection,
                        record['Id'],
                        status='Failed',
                        error_message=error_msg
                    )

                failure_count += 1
                error_summary.append(f"ID={record['Id']}: {error_msg}")

                # SECURITY: Log full error details to secure log file only
                logging.exception(f"✗ Failed to process ID={record['Id']}")

                # Continue processing other records (don't stop entire job)

        # SAFETY: If reprocess-all and successful, swap staging to production
        if reprocess_all:
            if failure_count == 0:
                logging.info("REPROCESS-ALL: All records processed successfully, swapping staging to production")
                swap_staging_to_production(target_db_connection)

                # Now mark all records as successfully processed
                mark_all_as_processed(source_db_connection)

                logging.info("REPROCESS-ALL: Staging tables promoted to production successfully")
            else:
                logging.error(f"REPROCESS-ALL: {failure_count} failures detected - ABORTING swap, staging tables retained for inspection")
                audit_logger.error(f"REPROCESS-ALL FAILED: {failure_count} errors, production data unchanged")
                raise Exception(f"Reprocess-all aborted due to {failure_count} failures - production data unchanged")

        # SECURITY: Log audit event
        log_audit_event(
            event_type='REPROCESS_ALL' if reprocess_all else 'NORMAL_RUN',
            records_processed=len(edi_records),
            records_succeeded=success_count,
            records_failed=failure_count,
            error_summary='; '.join(error_summary[:5]) if error_summary else None  # First 5 errors only
        )

        # Insert audit record to database
        insert_audit_log(
            target_db_connection,
            event_type='REPROCESS_ALL' if reprocess_all else 'NORMAL_RUN',
            records_processed=len(edi_records),
            records_succeeded=success_count,
            records_failed=failure_count,
            error_summary='; '.join(error_summary[:10]) if error_summary else None
        )

        logging.info(f"ETL Complete: {success_count} succeeded, {failure_count} failed")
        return success_count, failure_count

    finally:
        # SAFETY: Always reset staging mode flag, even if processing failed
        if reprocess_all:
            reset_staging_mode()


def reprocess_failed_records(source_conn, target_conn):
    """
    Reprocess only records that previously failed.
    SECURITY: Audit logged.
    """
    from config import audit_logger
    
    audit_logger.info("Reprocessing failed records")

    query = """
        UPDATE EDIGatewayInbound
        SET ReportingProcessStatus = NULL,
            ReportingProcessError = NULL,
            ReportingProcessed = NULL
        WHERE ReportingProcessStatus = 'Failed'
    """
    execute_query(source_conn, query)
    logging.info("Reset failed records for reprocessing")

    process_edi_transmissions(source_conn, target_conn, reprocess_all=False)