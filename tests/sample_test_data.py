"""
Sample JSON test data for EDI parsing tests.
Contains examples of both PREPACK and BULK orders.
"""

import sys
import os

# Add parent directory to path to import core modules
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, parent_dir)

# Use test configuration (console logging only, no file requirement)
sys.path.insert(0, os.path.dirname(__file__))
import config_test  # Import test config first to set up logging

# Sample PREPACK order (with BOM components)
SAMPLE_PREPACK_JSON = """{
  "PurchaseOrderHeader": {
    "PurchaseOrderNumber": "15826580",
    "CompanyCode": "KOHLS",
    "OrderDate": "20240115",
    "PurchaseOrder": {
      "RequestedShipDate": "20240201",
      "CancelDate": "20240215",
      "DepartmentNumber": "DEPT-123",
      "ReferencePOType": "PREPACK",
      "PurchaseOrderDetails": [
        {
          "VendorItemNumber": "STYLE-ABC",
          "GTIN": "00012345678905",
          "BuyerPartNumber": "SKU-001",
          "Quantity": 100,
          "UOMTypeCode": "EA",
          "UnitPrice": 25.50,
          "BOMDetails": [
            {
              "ColorDescription": "Navy Blue",
              "SizeDescription": "S",
              "GTIN": "00012345678901",
              "Quantity": 20,
              "UnitPrice": 25.50
            },
            {
              "ColorDescription": "Navy Blue",
              "SizeDescription": "M",
              "GTIN": "00012345678902",
              "Quantity": 40,
              "UnitPrice": 25.50
            },
            {
              "ColorDescription": "Navy Blue",
              "SizeDescription": "L",
              "GTIN": "00012345678903",
              "Quantity": 30,
              "UnitPrice": 25.50
            },
            {
              "ColorDescription": "Navy Blue",
              "SizeDescription": "XL",
              "GTIN": "00012345678904",
              "Quantity": 10,
              "UnitPrice": 25.50
            }
          ]
        },
        {
          "VendorItemNumber": "STYLE-XYZ",
          "GTIN": "00098765432105",
          "BuyerPartNumber": "SKU-002",
          "Quantity": 50,
          "UOMTypeCode": "EA",
          "UnitPrice": 32.00,
          "BOMDetails": [
            {
              "ColorDescription": "Black",
              "SizeDescription": "M",
              "GTIN": "00098765432101",
              "Quantity": 15,
              "UnitPrice": 32.00
            },
            {
              "ColorDescription": "Black",
              "SizeDescription": "L",
              "GTIN": "00098765432102",
              "Quantity": 25,
              "UnitPrice": 32.00
            },
            {
              "ColorDescription": "Black",
              "SizeDescription": "XL",
              "GTIN": "00098765432103",
              "Quantity": 10,
              "UnitPrice": 32.00
            }
          ]
        }
      ]
    }
  }
}"""

# Sample BULK order (no BOM components)
SAMPLE_BULK_JSON = """{
  "PurchaseOrderHeader": {
    "PurchaseOrderNumber": "PO-2024-5678",
    "CompanyCode": "AMAZON",
    "OrderDate": "20240120",
    "PurchaseOrder": {
      "RequestedShipDate": "20240205",
      "CancelDate": "20240220",
      "DepartmentNumber": "DEPT-456",
      "PurchaseOrderDetails": [
        {
          "VendorItemNumber": "WIDGET-100",
          "ColorDescription": "Red",
          "SizeDescription": "One Size",
          "GTIN": "00055555555501",
          "BuyerPartNumber": "AMZ-WIDGET-100",
          "Quantity": 500,
          "UOMTypeCode": "EA",
          "UnitPrice": 12.99,
          "RetailPrice": 24.99,
          "PackSize": 12
        },
        {
          "VendorItemNumber": "WIDGET-200",
          "ColorDescription": "Blue",
          "SizeDescription": "Large",
          "GTIN": "00055555555502",
          "BuyerPartNumber": "AMZ-WIDGET-200",
          "Quantity": 300,
          "UOMTypeCode": "EA",
          "UnitPrice": 15.50,
          "RetailPrice": 29.99,
          "PackSize": 6
        },
        {
          "VendorItemNumber": "WIDGET-300",
          "ColorDescription": "Green",
          "SizeDescription": "Medium",
          "GTIN": "00055555555503",
          "BuyerPartNumber": "AMZ-WIDGET-300",
          "Quantity": 200,
          "UOMTypeCode": "EA",
          "UnitPrice": 18.75,
          "RetailPrice": 34.99,
          "PackSize": 24
        }
      ]
    }
  }
}"""

# Minimal valid JSON
SAMPLE_MINIMAL_JSON = """{
  "PurchaseOrderHeader": {
    "PurchaseOrderNumber": "MIN-001",
    "CompanyCode": "TEST",
    "PurchaseOrder": {
      "PurchaseOrderDetails": [
        {
          "VendorItemNumber": "TEST-ITEM",
          "Quantity": 1
        }
      ]
    }
  }
}"""

# Invalid JSON (missing required fields)
SAMPLE_INVALID_JSON = """{
  "PurchaseOrderHeader": {
    "PurchaseOrderNumber": "INVALID-001",
    "PurchaseOrder": {
      "PurchaseOrderDetails": []
    }
  }
}"""


def run_all_samples():
    """Run tests on all sample data"""
    from test_transformers import test_edi_parsing, print_results

    samples = [
        ("PREPACK Order", SAMPLE_PREPACK_JSON),
        ("BULK Order", SAMPLE_BULK_JSON),
        ("Minimal Order", SAMPLE_MINIMAL_JSON),
        ("Invalid Order", SAMPLE_INVALID_JSON)
    ]

    for name, json_data in samples:
        print("\n" + "="*80)
        print(f"TEST: {name}")
        print("="*80)
        results = test_edi_parsing(json_data)
        print_results(results)
        input("\nPress Enter to continue to next test...")


if __name__ == "__main__":
    print("Sample EDI Test Data")
    print("="*80)
    print("\nAvailable samples:")
    print("  SAMPLE_PREPACK_JSON  - PREPACK order with BOM components")
    print("  SAMPLE_BULK_JSON     - BULK order with line items")
    print("  SAMPLE_MINIMAL_JSON  - Minimal valid order")
    print("  SAMPLE_INVALID_JSON  - Invalid order (for error testing)")
    print("\nUsage:")
    print("  from test_transformers import test_edi_parsing, print_results")
    print("  from sample_test_data import SAMPLE_PREPACK_JSON")
    print("  results = test_edi_parsing(SAMPLE_PREPACK_JSON)")
    print("  print_results(results)")
    print("\nOr run all samples:")
    print("  python sample_test_data.py")
    print("="*80)

    response = input("\nRun all sample tests? (y/n): ")
    if response.lower() == 'y':
        run_all_samples()
