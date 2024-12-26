// Copyright (c) 2024, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Inventory Count"] = {
	"filters": [
		{
			"fieldname": "item",
			"label": __("Barcode"),
			"fieldtype": "Link",
			"options": "Item"
		},

		{
			"fieldname": "warehouse",
			"label": __("Warehouse"),
			"fieldtype": "Link",
			"options": "Warehouse"
		}

	]
};
