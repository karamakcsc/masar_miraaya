# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    return columns(), data(filters), None

def data(filters):
    conditions = " 1=1 "
    if filters.get("item"):
        conditions += f" AND ti.name = '{filters.get('item')}'"
    if filters.get("item_group"):
        conditions += f" AND ti.item_group = '{filters.get('item_group')}' "
    if filters.get("brand"):
        conditions += f" AND ti.brand = '{filters.get('brand')}'"
    
    
    sql = frappe.db.sql(f"""
                            SELECT 
								ti.item_code AS `Item Code`,
								ti.item_name AS `Item Name`,
								ti.item_group AS `Category`, 
								tig.parent_item_group AS `Sub Category`,
								tig2.parent_item_group AS `Sub of Sub Category`,
								ti.brand AS `Brand`
							FROM 
								tabItem ti 
							INNER JOIN 
								`tabItem Group` tig ON tig.name = ti.item_group 
							LEFT JOIN 
								`tabItem Group` tig2 ON tig2.name = tig.parent_item_group
                            WHERE {conditions};
                        """)
    
    return sql

def columns():
    return [
        "Item Code: Link/Item:200",
        "Item Name: Data:200",
        "Category: Link/Item Group:200",
        "Sub Category: Link/Item Group:200",
        "Sub of Sub Category: Link/Item Group:200",
        "Brand: Link/Brand:200"
    ]