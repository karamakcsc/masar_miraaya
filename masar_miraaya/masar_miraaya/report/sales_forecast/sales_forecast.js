// Copyright (c) 2025, KCSC and contributors
// For license information, please see license.txt

frappe.query_reports["Sales Forecast"] = {
	"filters": [
		{
			"fieldname": "company",
			"label": "Company",
			"fieldtype": "Link",
			"options": "Company",
		},
		{
			"fieldname": "from_date",
			"label": "From Date",
			"fieldtype": "Date",
			"default": "Today - 90 days",
			"reqd": 1
		},
		{
			"fieldname": "to_date",
			"label": "To Date",
			"fieldtype": "Date",
			"default": "Today",
			"reqd": 1
		},
		{
			"fieldname": "based_on_document",
			"label": "Based On Document",
			"fieldtype": "Select",
			"options": "Sales Order\nSales Invoice",
			"default": "Sales Invoice",
			"reqd": 1
		},
		{
			"fieldname": "item_code",
			"label": "Item Code",
			"fieldtype": "Link",
			"options": "Item",
		},
		{
			"fieldname": "item_group",
			"label": "Item Group",
			"fieldtype": "Link",
			"options": "Item Group"
		},
		{
			"fieldname": "brand",
			"label": "Brand",
			"fieldtype": "Link",
			"options": "Brand"
		},
		{
			"fieldname": "months_for_forecast",
			"label": "Months for Forecast",
			"fieldtype": "Int",
			"default": 3
		},
		{
			"fieldname": "periodicity",
			"label": "Periodicity",
			"fieldtype": "Select",
			"options": "Monthly\nQuarterly\nYearly",
			"default": "Monthly",
			"reqd": 1
		},
		{
			"fieldname": "forecast_method",
			"label": "Forecast Method",
			"fieldtype": "Select",
			"options": "Simple Average\nWeighted Average\nLinear Regression",
			"default": "Simple Average"
		}
	]
};
