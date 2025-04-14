// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Count of Orders by Customer"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
		},
		{
			"fieldname": "customer",	
			"label": __("Customer"),
			"fieldtype": "Link",
			"options": "Customer",
		},
        {
            "fieldname": "customer_group",
            "label": __("Customer Group"),
            "fieldtype": "Link",
            "options": "Customer Group",
        },
		{
            "fieldname": "zero_orders",
            "label": __("Show Only Zero Orders"),
            "fieldtype": "Check",
            "default": 0,
        }
	]
};