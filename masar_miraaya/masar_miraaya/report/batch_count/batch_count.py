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
                                tsabe.batch_no, 
                                tb.reserved_qty, 
                                tb.actual_qty
                            FROM 
                                tabBin tb 
                            INNER JOIN
                                tabItem ti ON tb.item_code = ti.name
                            INNER JOIN 
                                `tabSerial and Batch Bundle` tsabb ON tb.item_code = tsabb.item_code
                            INNER JOIN
                                `tabSerial and Batch Entry` tsabe ON tsabb.name = tsabe.parent 
                            WHERE {conditions}
                        """)
    return sql

def columns():
    return [
		"Barcode:Link/Item:200",
        "Item Name:data:200",
        "UOM:Data:200",
        "Warehouse:Link/Warehouse:200",
        "Batch:Data:200",
        "Reserved Qty:Float:200",
        "Actual Qty:Float:200"
	]
