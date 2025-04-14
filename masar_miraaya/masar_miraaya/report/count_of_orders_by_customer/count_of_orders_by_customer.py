# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe import db

def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data


def get_columns():
    return [
        {"label": "Customer No", "fieldname": "customer_no", "fieldtype": "Link", "options": "Customer", "width": 250},
        {"label": "Customer Name", "fieldname": "customer_name", "fieldtype": "Data", "width": 250},
        {"label": "Email", "fieldname": "email", "fieldtype": "Data", "width": 250},
        {"label": "Phone No", "fieldname": "phone_no", "fieldtype": "Data", "width": 150},
        {"label": "Sales Order Count", "fieldname": "sales_order_count", "fieldtype": "Int", "width": 150}
    ]


def get_data(filters):
    if not filters:
        filters = {}
    
    conditions = []
    params = {}
    if filters.get('from_date') and filters.get('to_date'):
        if filters['from_date'] > filters['to_date']:
            frappe.throw("From Date should be less than To Date")
        conditions.append("tso.transaction_date BETWEEN %(from_date)s AND %(to_date)s")
        params.update({
            'from_date': filters['from_date'],
            'to_date': filters['to_date']
        })
    
    if filters.get('customer'):
        conditions.append("tc.name = %(customer)s")
        params['customer'] = filters['customer']
    
    if filters.get('customer_group'):
        conditions.append("tc.customer_group = %(customer_group)s")
        params['customer_group'] = filters['customer_group']
    
    where_clause = "WHERE 1=1"
    if conditions:
        where_clause += " AND " + " AND ".join(conditions)
    
    query = f"""
        SELECT 
            tc.name AS `customer_no`,
            tc.customer_name AS `customer_name`,
            tc.custom_email AS `email`,
            tc.custom_phone AS `phone_no`,
            IFNULL(COUNT(tso.name), 0) AS `sales_order_count`
        FROM 
            tabCustomer tc 
        LEFT JOIN 
            `tabSales Order` tso ON tc.name = tso.customer AND tso.docstatus = 1
            {f"AND tso.transaction_date BETWEEN %(from_date)s AND %(to_date)s" if filters.get('from_date') and filters.get('to_date') else ""}
        {where_clause}
        GROUP BY 
            tc.name
    """
    data = frappe.db.sql(query, params, as_dict=1)
    
    if filters.get('zero_orders'):
        data = [row for row in data if row['sales_order_count'] == 0]
    
    data = sorted(data, key=lambda x: x['sales_order_count'], reverse=True)
    
    return data