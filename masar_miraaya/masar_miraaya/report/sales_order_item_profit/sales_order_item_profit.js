// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Sales Order Item Profit"] = {
	"filters": [
		{
			"fieldname": "sales_order",
			"label": __("Sales Order"),
			"fieldtype": "Link",
			"options": "Sales Order"
		},
		{
			"fieldname": "item",
			"label": __("Item"),
			"fieldtype": "Link",
			"options": "Item"
		},
		{
			"fieldname": "warehouse",
			"label": __("Warehouse"),
			"fieldtype": "Link",
			"options": "Warehouse"
		},
		{
			"fieldname": "magento_id",
			"label": __("Magento ID"),
			"fieldtype": "Data"
		}
	]
};
