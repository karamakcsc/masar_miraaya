// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Item Cost Report"] = {
	"filters": [
		{
			"fieldname": "item",
			"label": __("Item"),
			"fieldtype": "Link",
			"options": "Item"
		},
		{
			"fieldname": "magento_id",
			"label": __("Magento ID"),
			"fieldtype": "Data"
		}
	]
};
