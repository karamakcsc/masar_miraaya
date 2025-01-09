# Copyright (c) 2024, KCSC and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    return columns(), data(filters), None

def data(filters):
    conditions = ' 1=1 '
    if filters.get('item'):
        conditions += f' AND tb.item_code = "{filters.get("item")}"'
    if filters.get('warehouse'):
        conditions += f' AND tb.warehouse = "{filters.get("warehouse")}"'
    if filters.get('mag_status'):
        conditions += f' AND ti.custom_magento_disabled = "{filters.get("mag_status")}"'
    if filters.get('erp_status'):
        conditions += f' AND ti.disabled = "{filters.get("erp_status")}"'
        
    sql = frappe.db.sql(f"""
                        	SELECT 
                                tb.item_code, 
                                ti.item_name, 
                                tb.stock_uom, 
                                tb.warehouse,
                                tb.actual_qty,
                                tb.reserved_qty, 
                                tb2.name,
								tb2.batch_qty,
								tb2.expiry_date,
                                CASE WHEN ti.disabled = 0 THEN "Enabled" ELSE "Disabled" END,
                                CASE WHEN ti.custom_magento_disabled = 0 THEN "Enabled" ELSE "Disabled" END
                            FROM 
                                tabBin tb 
                            INNER JOIN
                                tabItem ti ON tb.item_code = ti.name
                            INNER JOIN 
								`tabBatch` tb2 ON tb.item_code = tb2.item
                            WHERE {conditions}
                        """)
    return sql

def columns():
    return [
		"Barcode:Link/Item:250",
        "Item Name:data:300",
        "UOM:Data:200",
        "Warehouse:Link/Warehouse:200",
        "Actual Qty:Float:200",
        "Reserved Qty:Float:200",
        "Batch No:Data:200",
        "Batch Qty:Data:200",
        "Batch Expiry Date:Data:200",
        "Item ERP Status: Data:200",
        "Item Magento Status: Data:200"
	]
