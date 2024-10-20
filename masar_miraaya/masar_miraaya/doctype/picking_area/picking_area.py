# Copyright (c) 2024, KCSC and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PickingArea(Document):
	# def validate(self):
	# 	self.fetch_child_items()


	@frappe.whitelist()
	def fetch_child_items(self):
		self.items = []
		source_doc = frappe.get_doc("Sales Order", self.sales_order)
        
		for row in source_doc.items:
			self.append("items", {
				"item_code": row.item_code,
				"item_name": row.item_name,
				"qty": row.qty,
				"image": row.image,
				"amount": row.amount
			})