// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Pick List With Price"] = {
	"filters": [
		{
			"fieldname": "pick_list",
			"label": __("Pick List"),
			"fieldtype": "Link",
			"options": "Pick List",
			"get_query": function() {
				return {
					"filters": {
						"docstatus": 1
					}
				};
			},
		},

		{
			"fieldname": "item_code",
			"label": __("Item Code"),
			"fieldtype": "Link",
			"options": "Item"
		},
		{
			"fieldname": "sales_order",
			"label": __("Sales Order"),
			"fieldtype": "Link",
			"options": "Sales Order",
			"get_query": function() {
				return {
					"filters": {
						"docstatus": 1
					}
				};
			},
		}
	]
};
