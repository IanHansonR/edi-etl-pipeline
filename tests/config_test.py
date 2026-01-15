"""
Test configuration - uses console logging instead of file logging.
This allows unit tests to run without requiring C:\\EDI_Logs directory.
"""

import logging

# Configure console logging for tests (no file requirement)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]  # Console only
)

# Audit logger for tests (also console-based)
audit_logger = logging.getLogger('audit')
audit_handler = logging.StreamHandler()
audit_handler.setFormatter(logging.Formatter('%(asctime)s - AUDIT - %(message)s'))
audit_logger.addHandler(audit_handler)
audit_logger.setLevel(logging.INFO)

# Suppress audit logger propagation to avoid duplicate messages
audit_logger.propagate = False
