# Copyright (c) 2024, KCSC and contributors
# For license information, please see license.txt

# import frappe
from frappe.model.document import Document


class MagentoSync(Document):
	def validate(self):
		self.sync_check()
  
	def sync_check(self):
		self.sync == 0
  