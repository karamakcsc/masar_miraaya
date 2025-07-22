# Copyright (c) 2025, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from datetime import datetime


def execute(filters=None):
	data = get_data(filters)
	columns = get_columns(data)
	return data, columns

def get_data(filters):
	if filters.get("based_on_document"):
		from_doc = filters.get("based_on_document")
		from_child_doc = from_doc + " Item"
	if filters.get("periodicity"):
		periodicity = filters.get("periodicity")
		if periodicity == "Monthly":
			group_expr = "DATE_FORMAT(tsi.posting_date, '%%Y-%%m')"
		elif periodicity == "Quarterly":
			group_expr = "CONCAT(YEAR(tsi.posting_date), '-Q', QUARTER(tsi.posting_date))"
		elif periodicity == "Yearly":
			group_expr = "YEAR(tsi.posting_date)"
	sql = frappe.db.sql(f"""
		SELECT 
			tsii.item_code,
			ti.item_name,
			ti.item_group,
			ti.brand,
			{group_expr} AS period,
			SUM(tsii.qty) AS total_qty
		FROM `tab{from_doc}` tsi
		INNER JOIN `tab{from_child_doc}` tsii ON tsi.name = tsii.parent
		INNER JOIN `tabItem` ti ON tsii.item_code = ti.name
		GROUP BY tsii.item_code
		ORDER BY tsii.item_code
	""", as_dict=True)

	return sql

def get_columns(data):
	base_columns = [
		{"label": _("Item Code"), "fieldname": "item_code", "fieldtype": "Link", "options": "Item", "width": 120},
		{"label": _("Item Name"), "fieldname": "item_name", "fieldtype": "Data", "width": 200},
		{"label": _("Item Group"), "fieldname": "item_group", "fieldtype": "Link", "options": "Item Group", "width": 150},
		{"label": _("Brand"), "fieldname": "brand", "fieldtype": "Link", "options": "Brand", "width": 150},
	]
	
	period_keys = set()
	for row in data:
		for key in row:
			if key not in {"item_code", "item_name", "item_group", "brand"}:
				period_keys.add(key)

	# Sort period keys (e.g. '2024-01', '2024-02', etc.)
	period_columns = [{"label": p, "fieldname": p, "fieldtype": "Float", "width": 120} for p in sorted(period_keys)]
	return base_columns + period_columns