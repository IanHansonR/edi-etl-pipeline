"""
Unit tests for EDI transformation logic.
Tests parsing functions without requiring database connection.
"""

import json
from datetime import datetime
from typing import List, Dict, Any
import sys
import os

# Add parent directory to path to import core modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Use test configuration (console logging only, no file requirement)
sys.path.insert(0, os.path.dirname(__file__))
import config_test  # Import test config first to set up logging


class MockDatabase:
    """Mock database for testing - stores data in memory instead of SQL Server"""

    def __init__(self):
        self.headers: List[Dict[str, Any]] = []
        self.details: List[Dict[str, Any]] = []
        self.bom_components: List[Dict[str, Any]] = []
        self.next_id = 1

    def insert_header(self, **kwargs) -> int:
        """Simulate header insert and return ID"""
        header_id = self.next_id
        self.next_id += 1
        header = {'Id': header_id, **kwargs}
        self.headers.append(header)
        return header_id

    def insert_detail(self, **kwargs) -> int:
        """Simulate detail insert and return ID"""
        detail_id = self.next_id
        self.next_id += 1
        detail = {'Id': detail_id, **kwargs}
        self.details.append(detail)
        return detail_id

    def insert_bom_component(self, **kwargs) -> None:
        """Simulate BOM component insert"""
        component_id = self.next_id
        self.next_id += 1
        component = {'Id': component_id, **kwargs}
        self.bom_components.append(component)

    def get_next_version_number(self, customer_po: str, download_date: datetime) -> int:
        """Calculate version number based on existing headers"""
        count = sum(1 for h in self.headers
                   if h.get('customer_po') == customer_po
                   and h.get('download_date') < download_date)
        return count + 1

    def reset(self):
        """Clear all data"""
        self.headers.clear()
        self.details.clear()
        self.bom_components.clear()
        self.next_id = 1


def test_edi_parsing(json_input: str, source_table_id: int = 1,
                     download_date: datetime = None) -> Dict[str, Any]:
    """
    Test EDI parsing with JSON input and return structured output.

    Args:
        json_input: JSON string of EDI data
        source_table_id: Simulated source table ID
        download_date: Download date (defaults to now)

    Returns:
        Dictionary with parsed header, details, and BOM components
    """
    from transformers import detect_order_type

    # Import validate_json_structure directly to avoid config import issues
    import logging

    def validate_json_structure(edi_data: dict) -> None:
        """Validate JSON structure before processing"""
        if 'PurchaseOrderHeader' not in edi_data:
            raise ValueError("Missing required field: PurchaseOrderHeader")

        po_header = edi_data['PurchaseOrderHeader']
        required_fields = ['PurchaseOrderNumber', 'CompanyCode', 'PurchaseOrder']
        for field in required_fields:
            if field not in po_header:
                raise ValueError(f"Missing required field: PurchaseOrderHeader.{field}")

        po_number = po_header['PurchaseOrderNumber']
        if len(str(po_number)) > 50:
            raise ValueError(f"PurchaseOrderNumber exceeds maximum length: {len(po_number)}")

        po_details = po_header['PurchaseOrder']
        if 'PurchaseOrderDetails' not in po_details:
            raise ValueError("Missing required field: PurchaseOrder.PurchaseOrderDetails")

        if not isinstance(po_details['PurchaseOrderDetails'], list):
            raise ValueError("PurchaseOrderDetails must be an array")

        if len(po_details['PurchaseOrderDetails']) > 10000:
            raise ValueError(f"Excessive line items: {len(po_details['PurchaseOrderDetails'])}")

        logging.debug(f"JSON validation passed for PO {po_number}")

    # Parse JSON
    try:
        edi_data = json.loads(json_input)
    except json.JSONDecodeError as e:
        return {
            'error': f'Invalid JSON: {str(e)}',
            'success': False
        }

    # Validate structure
    try:
        validate_json_structure(edi_data)
    except ValueError as e:
        return {
            'error': f'Validation failed: {str(e)}',
            'success': False
        }

    # Set up mock database
    mock_db = MockDatabase()

    # Default download date
    if download_date is None:
        download_date = datetime.now()

    # Extract PO number
    customer_po = edi_data['PurchaseOrderHeader']['PurchaseOrderNumber']

    # Calculate version
    version = mock_db.get_next_version_number(customer_po, download_date)

    # Detect order type
    order_type = detect_order_type(edi_data)

    # Process based on type (using modified functions that work with mock)
    try:
        if order_type == 'PREPACK':
            process_prepack_with_mock(
                edi_data=edi_data,
                download_date=download_date,
                source_table_id=source_table_id,
                version=version,
                mock_db=mock_db
            )
        else:
            process_bulk_with_mock(
                edi_data=edi_data,
                download_date=download_date,
                source_table_id=source_table_id,
                version=version,
                mock_db=mock_db
            )
    except Exception as e:
        return {
            'error': f'Processing failed: {str(e)}',
            'success': False
        }

    # Return structured results
    return {
        'success': True,
        'order_type': order_type,
        'customer_po': customer_po,
        'version': version,
        'header': mock_db.headers[0] if mock_db.headers else None,
        'details': mock_db.details,
        'bom_components': mock_db.bom_components,
        'summary': {
            'total_detail_rows': len(mock_db.details),
            'total_bom_components': len(mock_db.bom_components)
        }
    }


def process_prepack_with_mock(edi_data, download_date, source_table_id, version, mock_db):
    """Process PREPACK order using mock database"""
    from data_validation import safe_parse_date, safe_int_conversion, safe_float_conversion, parse_destination_dc

    po_header = edi_data['PurchaseOrderHeader']
    po_details = po_header['PurchaseOrder']

    # Insert header
    header_id = mock_db.insert_header(
        customer_po=po_header['PurchaseOrderNumber'],
        company=po_header.get('CompanyCode'),
        order_date=safe_parse_date(po_header.get('OrderDate')),
        start_date=safe_parse_date(po_details.get('RequestedShipDate')),
        complete_date=safe_parse_date(po_details.get('CancelDate')),
        department=po_details.get('DepartmentNumber'),
        download_date=download_date,
        po_type='PREPACK',
        version=version,
        source_table_id=source_table_id
    )

    # Process each line item
    for line_item in po_details.get('PurchaseOrderDetails', []):
        # Get color from first BOM component
        color = None
        if line_item.get('BOMDetails') and len(line_item['BOMDetails']) > 0:
            color = line_item['BOMDetails'][0].get('ColorDescription')

        detail_id = mock_db.insert_detail(
            header_id=header_id,
            style=line_item.get('VendorItemNumber'),
            color=color,
            size=None,
            qty=safe_int_conversion(line_item.get('Quantity', 0)),
            upc=line_item.get('GTIN'),
            sku=line_item.get('BuyerPartNumber'),
            uom=line_item.get('UOMTypeCode'),
            unit_price=safe_float_conversion(line_item.get('UnitPrice', 0)),
            retail_price=None,
            inner_pack=None,
            qty_per_inner_pack=None,
            dc=parse_destination_dc(line_item.get('DestinationInfo')),
            store_number=None,
            is_bom=True
        )

        # Insert BOM components
        for bom_component in line_item.get('BOMDetails', []):
            mock_db.insert_bom_component(
                detail_id=detail_id,
                component_sku=bom_component.get('GTIN'),
                component_size=bom_component.get('SizeDescription'),
                component_qty=safe_int_conversion(bom_component.get('Quantity', 1)),
                component_unit_price=safe_float_conversion(bom_component.get('UnitPrice', 0)),
                component_retail_price=None
            )


def process_bulk_with_mock(edi_data, download_date, source_table_id, version, mock_db):
    """Process BULK order using mock database"""
    from data_validation import safe_parse_date, safe_int_conversion, safe_float_conversion, parse_destination_dc

    po_header = edi_data['PurchaseOrderHeader']
    po_details = po_header['PurchaseOrder']

    # Insert header
    header_id = mock_db.insert_header(
        customer_po=po_header['PurchaseOrderNumber'],
        company=po_header.get('CompanyCode'),
        order_date=safe_parse_date(po_header.get('OrderDate')),
        start_date=safe_parse_date(po_details.get('RequestedShipDate')),
        complete_date=safe_parse_date(po_details.get('CancelDate')),
        department=po_details.get('DepartmentNumber'),
        download_date=download_date,
        po_type='BULK',
        version=version,
        source_table_id=source_table_id
    )

    # Process each line item
    for line_item in po_details.get('PurchaseOrderDetails', []):
        retail_price_val = line_item.get('RetailPrice')
        retail_price = safe_float_conversion(retail_price_val) if retail_price_val else None

        pack_size_val = line_item.get('PackSize')
        inner_pack = safe_int_conversion(pack_size_val) if pack_size_val else None

        mock_db.insert_detail(
            header_id=header_id,
            style=line_item.get('VendorItemNumber'),
            color=line_item.get('ColorDescription'),
            size=line_item.get('SizeDescription'),
            qty=safe_int_conversion(line_item.get('Quantity', 0)),
            upc=line_item.get('GTIN'),
            sku=line_item.get('BuyerPartNumber'),
            uom=line_item.get('UOMTypeCode'),
            unit_price=safe_float_conversion(line_item.get('UnitPrice', 0)),
            retail_price=retail_price,
            inner_pack=inner_pack,
            qty_per_inner_pack=None,
            dc=parse_destination_dc(line_item.get('DestinationInfo')),
            store_number=None,
            is_bom=False
        )


def print_results(results: Dict[str, Any]):
    """Pretty print the parsing results in table format"""
    if not results.get('success'):
        print(f"\n[ERROR] {results.get('error')}")
        return

    print(f"\n[SUCCESS] - Parsed {results['order_type']} order")
    print(f"PO Number: {results['customer_po']}")
    print(f"Version: {results['version']}")

    # Header table
    print("\n" + "="*80)
    print("HEADER")
    print("="*80)
    header = results['header']
    if header:
        for key, value in header.items():
            if key != 'Id':
                print(f"{key:20s}: {value}")

    # Details table
    print("\n" + "="*80)
    print(f"DETAILS ({results['summary']['total_detail_rows']} rows)")
    print("="*80)

    if results['details']:
        # Print header row
        keys = [k for k in results['details'][0].keys() if k not in ['Id', 'header_id']]
        print(f"{'Row':<4} | " + " | ".join(f"{k:<15}" for k in keys))
        print("-" * (6 + len(keys) * 18))

        # Print data rows
        for idx, detail in enumerate(results['details'], 1):
            values = [str(detail.get(k, ''))[:15] for k in keys]
            print(f"{idx:<4} | " + " | ".join(f"{v:<15}" for v in values))

    # BOM components table (if any)
    if results['bom_components']:
        print("\n" + "="*80)
        print(f"BOM COMPONENTS ({results['summary']['total_bom_components']} rows)")
        print("="*80)

        keys = [k for k in results['bom_components'][0].keys() if k not in ['Id', 'detail_id']]
        print(f"{'Row':<4} | " + " | ".join(f"{k:<15}" for k in keys))
        print("-" * (6 + len(keys) * 18))

        for idx, component in enumerate(results['bom_components'], 1):
            values = [str(component.get(k, ''))[:15] for k in keys]
            print(f"{idx:<4} | " + " | ".join(f"{v:<15}" for v in values))

    print("\n" + "="*80)


def run_test_from_file(json_file_path: str):
    """Load JSON from file and test parsing"""
    try:
        with open(json_file_path, 'r') as f:
            json_input = f.read()

        results = test_edi_parsing(json_input)
        print_results(results)
        return results
    except FileNotFoundError:
        print(f"❌ ERROR: File not found: {json_file_path}")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")


# Example usage for interactive testing
if __name__ == "__main__":
    print("EDI Transformation Unit Tests")
    print("="*80)
    print("\nUsage Options:")
    print("1. Paste JSON directly and call test_edi_parsing(json_string)")
    print("2. Load from file: run_test_from_file('path/to/file.json')")
    print("\nExample:")
    print('  json_input = """<paste your JSON here>"""')
    print('  results = test_edi_parsing(json_input)')
    print('  print_results(results)')
    print("\n" + "="*80)
