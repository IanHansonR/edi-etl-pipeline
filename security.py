import re
import logging
from typing import Optional
from config import audit_logger


def sanitize_error_message(error: Exception) -> str:
    """
    SECURITY: Sanitize error messages before storing in database.
    Prevents leaking file paths, server names, or connection strings.
    """
    error_type = type(error).__name__
    error_msg = str(error)

    # Truncate to prevent excessive data in database
    if len(error_msg) > 500:
        error_msg = error_msg[:497] + "..."

    # Remove potentially sensitive patterns
    sensitive_patterns = [
        r'C:\\[^\s]+',  # File paths
        r'Server=[^;]+',  # Server names
        r'Password=[^;]+',  # Passwords (shouldn't exist, but belt-and-suspenders)
    ]

    for pattern in sensitive_patterns:
        error_msg = re.sub(pattern, '[REDACTED]', error_msg)

    return f"{error_type}: {error_msg}"


def log_audit_event(event_type: str, records_processed: int,
                    records_succeeded: int, records_failed: int,
                    error_summary: Optional[str] = None):
    """
    SECURITY: Log audit trail of ETL operations.
    Critical for compliance and troubleshooting.
    """
    audit_logger.info(
        f"EventType={event_type} | "
        f"Processed={records_processed} | "
        f"Succeeded={records_succeeded} | "
        f"Failed={records_failed} | "
        f"Errors={error_summary or 'None'}"
    )


def validate_json_structure(edi_data: dict) -> None:
    """
    SECURITY: Validate JSON structure before processing.
    Prevents crashes from malformed or malicious data.
    """
    # Required top-level structure
    if 'PurchaseOrderHeader' not in edi_data:
        raise ValueError("Missing required field: PurchaseOrderHeader")

    po_header = edi_data['PurchaseOrderHeader']

    # Required header fields
    required_fields = ['PurchaseOrderNumber', 'CompanyCode', 'PurchaseOrder']
    for field in required_fields:
        if field not in po_header:
            raise ValueError(f"Missing required field: PurchaseOrderHeader.{field}")

    # Validate PurchaseOrderNumber is not suspiciously long
    po_number = po_header['PurchaseOrderNumber']
    if len(str(po_number)) > 50:
        raise ValueError(f"PurchaseOrderNumber exceeds maximum length: {len(po_number)}")

    # Validate PurchaseOrder structure
    po_details = po_header['PurchaseOrder']
    if 'PurchaseOrderDetails' not in po_details:
        raise ValueError("Missing required field: PurchaseOrder.PurchaseOrderDetails")

    if not isinstance(po_details['PurchaseOrderDetails'], list):
        raise ValueError("PurchaseOrderDetails must be an array")

    # SECURITY: Limit on number of line items (prevent DOS)
    if len(po_details['PurchaseOrderDetails']) > 10000:
        raise ValueError(f"Excessive line items: {len(po_details['PurchaseOrderDetails'])}")

    logging.debug(f"JSON validation passed for PO {po_number}")