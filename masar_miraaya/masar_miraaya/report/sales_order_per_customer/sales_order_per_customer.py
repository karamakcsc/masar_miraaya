# Copyright (c) 2024, KCSC and contributors
# For license information, please see license.txt

import frappe

def execute(filters=None):
    return columns(), data(filters), None

def data(filters):
    conditions = " 1=1 "
    _from, to = filters.get('from_date'), filters.get('to_date')
    if filters.get("customer"):
        conditions += f" AND tso.customer = '{filters.get('customer')}'"
    if _from and to:
        conditions += f" AND tso.transaction_date BETWEEN '{_from}' AND '{to}' "
    
    
    sql = frappe.db.sql(f"""
                            SELECT 
                                tso.customer, 
                                tso.customer_name, 
                                COUNT(tso.name) AS `Sales Order Count`,
                                SUM(tso.total_qty) AS `Sales Orders Qty` 
                            FROM `tabSales Order` tso 
                            WHERE {conditions} AND tso.docstatus = 1
                            GROUP BY tso.customer
                        """)
    
    return sql

def columns():
    return [
        "Customer: Link/Customer:200",
        "Customer Name: Data:200",
        "Sales Order Count: Int:200",
        "Sales Orders Qty: Int:200"
    ]
