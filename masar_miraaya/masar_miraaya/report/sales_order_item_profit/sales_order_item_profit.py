# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    return columns(), data(filters), None

def data(filters):
    conditions = " 1=1 "
    if filters.get("sales_order"):
        conditions += f" AND tso.sales_order = '{filters.get('sales_order')}'"
    if filters.get("item"):
        conditions += f" AND tsoi.item = '{filters.get('item')}' "
    if filters.get("warehouse"):
        conditions += f" AND tsoi.warehouse = '{filters.get('warehouse')}'"
    if filters.get("magento_id"):
        conditions += f" AND tso.custom_magento_id LIKE '%{filters.get('magento_id')}%'"
    
    
    sql = frappe.db.sql(f"""
                            SELECT DISTINCT
								tso.name AS `Sales Order`,
								tso.custom_magento_id AS `Magento ID`, 
								tsoi.item_code AS `Item Code`, 
								tsoi.item_name AS `Item Name`, 
								tsoi.warehouse AS `Warehouse`,
								tsoi.qty AS `Quantity`,
								tsoi.valuation_rate AS `Valuation Rate`,
								tsoi.rate AS `Rate`,
								SUM(CASE WHEN tip.price_list = 'Standard Buying' THEN tip.price_list_rate END) AS `Buying Rate`,
								tsoi.gross_profit AS `Profit (Valuation Rate)`,
								SUM((tsoi.rate - 
									CASE 
										WHEN tip.price_list = 'Standard Buying' THEN tip.price_list_rate 
									END)) AS `Profit (Buying Rate)`
							FROM `tabSales Order` tso
							INNER JOIN `tabSales Order Item` tsoi ON tsoi.parent = tso.name
							INNER JOIN `tabItem Price` tip ON tsoi.item_code = tip.item_code
							WHERE {conditions} AND tso.docstatus = 1
							GROUP BY tsoi.item_code, tso.name
                        """)
    
    return sql

def columns():
    return [
        "Sales Order: Link/Sales Order:200",
        "Magento ID: Data:200",
        "Item Code: Link/Item:200",
        "Item Name: Data:200",
        "Warehouse: Link/Warehouse:200",
        "Qty: Float:200",
        "Valuation Rate: Float:200",
        "Rate: Float:200",
        "Buying Rate: Float:200",
        "Profit (Valuation Rate): Float:200",
        "Profit (Buying Rate): Float:200"
    ]