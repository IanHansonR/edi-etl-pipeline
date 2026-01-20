import logging
from data_validation import safe_parse_date, safe_int_conversion, safe_float_conversion, parse_destination_dc
from database import insert_header, insert_detail, insert_bom_component


def process_prepack_order(edi_data, download_date, source_table_id, version, db_connection):
    """
    Process PREPACK orders with security validations. Made for 88 Kohls.
    """
    # 1. Extract header info
    po_header = edi_data['PurchaseOrderHeader']
    po_details = po_header['PurchaseOrder']

    # 2. Insert header with safe date parsing
    header_id = insert_header(
        customer_po=po_header['PurchaseOrderNumber'],
        company=po_header.get('CompanyCode'),
        order_date=safe_parse_date(po_header.get('OrderDate')),
        start_date=safe_parse_date(po_details.get('RequestedShipDate')),
        complete_date=safe_parse_date(po_details.get('CancelDate')),
        department=po_details.get('DepartmentNumber'),
        download_date=download_date,
        po_type='PREPACK',
        version=version,
        source_table_id=source_table_id,
        db_connection=db_connection
    )

    # 3. Process each PurchaseOrderDetail (each is one BOM type)
    for line_item in po_details.get('PurchaseOrderDetails', []):
        # Get color from FIRST BOM component (all components share same color)
        color = None
        if line_item.get('BOMDetails') and len(line_item['BOMDetails']) > 0:
            color = line_item['BOMDetails'][0].get('ColorDescription')

        # SECURITY: Safe numeric conversions
        detail_id = insert_detail(
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
            inner_pack=safe_int_conversion(line_item.get('Pack', 1)),  # edit
            qty_per_inner_pack=safe_int_conversion(line_item.get('PackSize', 1)), # edit
            dc=parse_destination_dc(line_item.get('DestinationInfo')),
            store_number=None,
            is_bom=True,
            db_connection=db_connection
        )

        # 4. Insert BOM components
        for bom_component in line_item.get('BOMDetails', []):
            insert_bom_component(
                detail_id=detail_id,
                component_sku=bom_component.get('GTIN'),
                component_size=bom_component.get('SizeDescription'),
                component_qty=safe_int_conversion(bom_component.get('Quantity', 1)),
                component_unit_price=safe_float_conversion(bom_component.get('UnitPrice', 0)),
                component_retail_price=safe_float_conversion(bom_component.get('RetailPrice',0)), # edit
                db_connection=db_connection
            )


def process_bulk_order(edi_data, download_date, source_table_id, version, db_connection):
    """
    Process BULK orders with security validations. Made for 88 Kohls.
    """
    # 1. Extract header info
    po_header = edi_data['PurchaseOrderHeader']
    po_details = po_header['PurchaseOrder']

    # 2. Insert header with safe date parsing
    header_id = insert_header(
        customer_po=po_header['PurchaseOrderNumber'],
        company=po_header.get('CompanyCode'),
        order_date=safe_parse_date(po_header.get('OrderDate')),
        start_date=safe_parse_date(po_details.get('RequestedShipDate')),
        complete_date=safe_parse_date(po_details.get('CancelDate')),
        department=po_details.get('DepartmentNumber'),
        download_date=download_date,
        po_type='BULK',
        version=version,
        source_table_id=source_table_id,
        db_connection=db_connection
    )

    # 3. Insert one detail row per line item
    for line_item in po_details.get('PurchaseOrderDetails', []):
        # SECURITY: Safe numeric conversions and null handling
        retail_price_val = line_item.get('RetailPrice')
        retail_price = safe_float_conversion(retail_price_val) if retail_price_val else None

        pack_size_val = line_item.get('PackSize')
        inner_pack = safe_int_conversion(pack_size_val) if pack_size_val else None

        pack_qty = line_item.get('Pack') # edit2
        qty_per_inner_pack = safe_int_conversion(pack_qty) if pack_qty else None # edit2

        insert_detail(
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
            qty_per_inner_pack=qty_per_inner_pack, # edit2
            dc=parse_destination_dc(line_item.get('DestinationInfo')),
            store_number=None,
            is_bom=False,
            db_connection=db_connection
        )


def detect_order_type(edi_data):
    """Determine order type from JSON content"""
    # Check for Kohl's structure
    if 'PurchaseOrderHeader' in edi_data:
        po_details = edi_data['PurchaseOrderHeader'].get('PurchaseOrder', {})

        # Check ReferencePOType
        if po_details.get('ReferencePOType') == 'PREPACK':
            return 'PREPACK'

        # Or check for presence of BOM data in any line item
        for detail in po_details.get('PurchaseOrderDetails', []):
            if 'BOMDetails' in detail and detail['BOMDetails']:
                return 'PREPACK'

    return 'BULK'  # Default to BULK for all other type