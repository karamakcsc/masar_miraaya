# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe


def execute(filters=None):
	return columns(), data(filters)


def data(filters):
	conditions = " 1=1 "
	if filters.get("pick_list"):
		conditions += f" AND tpl.name = '{filters.get('pick_list')}'"
	if filters.get("item_code"):
		conditions += f" AND tpli.item_code = '{filters.get('item_code')}'"
	if filters.get("sales_order"):
		conditions += f" AND tpli.sales_order = '{filters.get('sales_order')}'"

	sql = frappe.db.sql(f"""
        SELECT 
			tpl.name AS `Pick List`, 
			tpli.item_code AS `Item Code`, 
			tpli.item_name AS `Item Name`, 
			tpli.item_group AS `Item Group`, 
			tpli.warehouse AS `Warehouse`, 
			tpli.batch_no AS `Batch No`,
			tpli.qty AS `Qty`, 
			tsoi.rate AS `Selling Rate`, 
			tpli.sales_order AS `Sales Order`,
			CASE 
				WHEN tpl.custom_packed = 1 THEN "Packed"
				ELSE "Not Packed"
			END AS `Packing Status`
		FROM `tabPick List` tpl 
		INNER JOIN `tabPick List Item` tpli ON tpl.name = tpli.parent 
		INNER JOIN `tabSales Order` tso ON tpli.sales_order = tso.name
		INNER JOIN `tabSales Order Item` tsoi ON tpli.sales_order = tsoi.parent AND tpli.sales_order_item = tsoi.name 
		WHERE {conditions} AND tpl.docstatus = 1 AND tso.docstatus = 1
	""")

	return sql

def columns():
	return[
		"Pick List:Link/Pick List:250",
		"Item Code:Link/Item:150",
		"Item Name:Data:200",
		"Item Group:Link/Item Group:150",
		"Warehouse:Link/Warehouse:150",
		"Batch No:Link/Batch:150",
		"Qty:Float:100",
		"Selling Rate:Currency:100",
		"Sales Order:Link/Sales Order:150",
		"Packing Status:Data:150"
	]