# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    return columns(), data(filters), None

def data(filters):
    conditions = " 1=1 "
    if filters.get("item"):
        conditions += f" AND ti.item LIKE '%{filters.get('item')}%' "
    if filters.get("magento_id"):
        conditions += f" AND ti.custom_item_id LIKE '%{filters.get('magento_id')}%'"
    
    
    sql = frappe.db.sql(f"""
				SELECT 
					ti.name AS `Item Code`, 
					ti.item_name AS `Item Name`,
					ti.custom_item_id AS `Magento ID`,
                    tb.valuation_rate,
					SUM(CASE WHEN tip.price_list = 'Standard Buying' THEN tip.price_list_rate END) AS `Buying Price`,
					SUM(CASE WHEN tip.price_list = 'Standard Selling' THEN tip.price_list_rate END) AS `Selling Price`,
                    SUM(CASE WHEN tip.price_list = 'Standard Selling' THEN tip.price_list_rate END) - 
					SUM(CASE WHEN tip.price_list = 'Standard Buying' THEN tip.price_list_rate END) AS `Price Difference`
				FROM tabItem ti
				INNER JOIN `tabItem Price` tip ON ti.name = tip.item_code
				INNER JOIN tabBin tb ON ti.name = tb.item_code
				WHERE {conditions} AND tb.warehouse NOT IN ('Jadria Products - MC', 'Delivery - MC')
				GROUP BY ti.name
                        """)
    
    return sql

def columns():
    return [
        "Item Code: Link/Item:200",
        "Item Name: Data:200",
        "Magento ID: Data:200",
        "Valuation Rate: Float:200",
        "Buying Price: Float:200",
        "Selling Price: Float:200",
        "Price Difference: Float:200"
    ]