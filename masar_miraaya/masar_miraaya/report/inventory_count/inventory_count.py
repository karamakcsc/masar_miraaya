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
        
    sql = frappe.db.sql(f"""
                        	SELECT 
                                tb.item_code, 
                                ti.item_name, 
                                tb.stock_uom, 
                                tb.warehouse, 
                                tb.reserved_qty, 
                                tb.actual_qty,
                                CASE WHEN ti.disabled = 0 THEN "Enabled" ELSE "Disabled" END
                            FROM 
                                tabBin tb 
                            INNER JOIN
                                tabItem ti ON tb.item_code = ti.name
                            WHERE {conditions}
                        """)
    return sql

def columns():
    return [
		"Barcode:Link/Item:250",
        "Item Name:data:300",
        "UOM:Data:200",
        "Warehouse:Link/Warehouse:200",
        "Reserved Qty:Float:200",
        "Actual Qty:Float:200",
        "Item Status: Data:200"
	]
