import argparse
import logging
from config import connect_to_database, audit_logger
from security import sanitize_error_message
from etl_processor import process_edi_transmissions, reprocess_failed_records


def main():
    """
    Main entry point with security considerations.
    """
    parser = argparse.ArgumentParser(description='EDI Reporting ETL Pipeline')
    parser.add_argument(
        '--reprocess-all',
        action='store_true',
        help='Reprocess ALL records (for testing/development) - USE WITH CAUTION'
    )
    parser.add_argument(
        '--reprocess-failed',
        action='store_true',
        help='Reprocess only previously failed records'
    )

    args = parser.parse_args()

    # SECURITY: Log command-line arguments (audit trail)
    logging.info(f"ETL job started with arguments: {args}")

    # SECURITY: Warning for reprocess-all
    if args.reprocess_all:
        logging.warning("REPROCESS-ALL mode enabled - will rebuild data via staging tables")
        audit_logger.warning("REPROCESS-ALL mode enabled")

    source_conn = None
    target_conn = None

    try:
        # SECURITY: Connect using Windows Authentication
        source_conn = connect_to_database('source')
        target_conn = connect_to_database('reporting')

        if args.reprocess_failed:
            # Only reprocess failed records
            reprocess_failed_records(source_conn, target_conn)
        else:
            # Normal processing (or full reprocess if flag set)
            process_edi_transmissions(
                source_conn,
                target_conn,
                reprocess_all=args.reprocess_all
            )

        logging.info("ETL job completed successfully")

    except Exception as e:
        # SECURITY: Sanitize error before logging
        error_msg = sanitize_error_message(e)
        logging.error(f"ETL job failed: {error_msg}")
        logging.exception("Full exception details:")

        # SECURITY: Send alert (implement based on your alerting system)
        # send_alert(f"EDI ETL Error: {error_msg}")

        raise
    finally:
        # Always close connections
        if source_conn:
            source_conn.close()
            logging.info("Source connection closed")
        if target_conn:
            target_conn.close()
            logging.info("Reporting connection closed")


if __name__ == "__main__":
    main()

